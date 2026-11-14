import os
import json
import boto3
import traceback
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
from nhl_api import get_player_info, get_team_rosters
from age_calculator import find_age
from random import choice
from data import TEAM_DIVISIONS_CONFERENCES, PLAYER_IDS, VIDEO_SOURCES
from pwhl_api import get_pwhl_rosters
from pwhl_data import PWHL_PLAYERS, PWHL_TEAM_CONFERENCES, PWHL_NATIONS, HOMETOWN_NATIONS
from dotenv import load_dotenv
from pathlib import Path

# Load secrets.env from the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / "secrets.env"
load_dotenv(dotenv_path=ENV_PATH)

# Local paths for writing the files
NHL_LOCAL_CACHE_PATH = ROOT_DIR / "player_data.json"
PWHL_LOCAL_CACHE_PATH = ROOT_DIR / "pwhl_player_data.json"

# Bucket keys
NHL_S3_CACHE_KEY = "player_data.json"
PWHL_S3_CACHE_KEY = "pwhl_player_data.json"

# Fetch existing cache from R2
def load_cache(s3, bucket, key):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception:
        return {"unused_daily_players": []} # Triggers if the file DNE

# Retrieve a player's existing results or initialise them
def get_results(existing_cached_players, name, max_guesses):
    default_results = {str(i): 0 for i in range(1, max_guesses + 1)}
    default_results.update({"X": 0, "total_guesses": 0})
    return existing_cached_players.get(name, {}).get("results", default_results)

# Choose the daily player and update the unused list and daily history
def pick_daily_player(cache_dictionary, eligible):

    # Retrieve daily history
    daily_history = cache_dictionary.get("daily_history", {})

    # Keep only eligible names from the saved list
    unused_list = [n for n in cache_dictionary.get("unused_daily_players", []) if n in eligible]

    # Add video players who have not yet been a daily answer
    used_names = set(daily_history.values())
    for name in eligible:
        if name not in used_names and name not in unused_list:
            unused_list.append(name)

    # Refill from eligible players only, avoiding an immediate repeat of yesterday's answer
    if not unused_list:
        last_daily = daily_history.get(str(len(daily_history)))
        unused_list = [n for n in eligible if n != last_daily] or eligible

    daily_name = choice(unused_list)
    unused_list.remove(daily_name)

    # Append the new daily player to the daily history
    next_index = str(len(daily_history) + 1)
    daily_history[next_index] = daily_name

    return daily_name, unused_list, daily_history

# Keep the current daily player, unused list, and daily history
def keep_daily_player(cache_dictionary):
    return cache_dictionary["daily_name"], cache_dictionary.get("unused_daily_players", []), cache_dictionary.get("daily_history", {})

# Save local copy and upload to Cloudflare R2
def save_cache(s3, bucket, key, local_path, player_dict, video_sources, daily_name, unused_list, daily_history, updated=None):

    # Update file with new date (unless one is kept) and player dictionary
    est = ZoneInfo("America/New_York")
    new_cache = {
        "updated": updated or datetime.now(tz=est).strftime("%Y-%m-%d"),
        "players": player_dict,
        "unused_daily_players": unused_list,
        "daily_name": daily_name,
        "daily_history": daily_history,
        "video_sources": video_sources
    }

    # Prepare JSON data
    json_data = json.dumps(new_cache, ensure_ascii=False, indent=4)

    # Save local copy
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(json_data)

    # Upload to Cloudflare R2
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json_data.encode("utf-8"),
        ContentType="application/json",
        CacheControl="no-cache, no-store, must-revalidate"
    )

# Create a unique name for each player, keeping existing names so results are preserved
def get_player_name(player, player_id, name_counts):
    name = f"{player['firstName']['default']} {player['lastName']['default']}"

    if name_counts[name] > 1 and PLAYER_IDS.get(name) != player_id: # Duplicate name
        name = f"{name} ({player['positionCode']})"

    return name

# Create and upload the NHL player data
def update_nhl(s3, bucket, pick_daily=True):

    # Retrieve every rostered player
    roster_players = get_team_rosters(TEAM_DIVISIONS_CONFERENCES.keys())

    # Retrieve players missing from rosters (e.g. injured reserve) so no video players are lost
    missing_ids = [player_id for player_id in PLAYER_IDS.values() if player_id not in roster_players]
    for player_data in get_player_info(missing_ids):
        if player_data.get("currentTeamAbbrev") not in TEAM_DIVISIONS_CONFERENCES: # No longer on an NHL team
            continue

        player_data["team"] = player_data["currentTeamAbbrev"]
        player_data["positionCode"] = player_data["position"]
        roster_players[player_data["playerId"]] = player_data

    # Count names to find players who share one
    name_counts = Counter(f"{p['firstName']['default']} {p['lastName']['default']}" for p in roster_players.values())

    # Fetch existing cache from R2 after the API calls so fewer submitted results are overwritten
    cache_dictionary = load_cache(s3, bucket, NHL_S3_CACHE_KEY)

    # Retrieve all players currently in the game
    existing_cached_players = cache_dictionary.get("players", {})

    # Create formatted dictionary with player data, sorted by name
    player_dict = {}
    for player_id, player_data in roster_players.items():
        name = get_player_name(player_data, player_id, name_counts)
        player_dict[name] = {
            "team": player_data["team"],
            "division": TEAM_DIVISIONS_CONFERENCES[player_data["team"]][0],
            "number": player_data["sweaterNumber"],
            "nation": player_data["birthCountry"],
            "age": find_age(player_data["birthDate"]),
            "conference": TEAM_DIVISIONS_CONFERENCES[player_data["team"]][1],
            "id": player_id,
            "results": get_results(existing_cached_players, name, 8)
        }
    player_dict = dict(sorted(player_dict.items()))

    # Only players with a video who are in the game can be daily answers
    eligible = [name for name in VIDEO_SOURCES if name in player_dict]

    # Choose a new daily player, or keep the current one when only refreshing players
    if pick_daily or "daily_name" not in cache_dictionary:
        daily_name, unused_list, daily_history = pick_daily_player(cache_dictionary, eligible)
        updated = None
    else:
        daily_name, unused_list, daily_history = keep_daily_player(cache_dictionary)
        updated = cache_dictionary["updated"] # Keep the date so today's game stays locked for those who played

    save_cache(s3, bucket, NHL_S3_CACHE_KEY, NHL_LOCAL_CACHE_PATH, player_dict, VIDEO_SOURCES, daily_name, unused_list, daily_history, updated)

# Retrieve a PWHL player's nation, using their hometown if their birth country is missing
def get_pwhl_nation(player):
    if player["birthcntry"] in PWHL_NATIONS:
        return PWHL_NATIONS[player["birthcntry"]]

    hometown_region = player["hometown"].split(",")[-1].strip()
    return HOMETOWN_NATIONS.get(hometown_region)

# Create and upload the PWHL player data
def update_pwhl(s3, bucket, pick_daily=True):

    # Retrieve every rostered player, excluding camp invitees
    roster_players = [player_data for player_data in get_pwhl_rosters().values() if player_data["status"] != "Camp Invitee"]

    # Count names to find players who share one
    name_counts = Counter(player_data["name"] for player_data in roster_players)

    # Create formatted dictionary with player data from the rosters
    player_dict = {}
    for player_data in roster_players:
        name = player_data["name"]
        if name_counts[name] > 1: # Duplicate name
            name = f"{name} ({player_data['position']})"

        nation = get_pwhl_nation(player_data)
        if not nation or not player_data["tp_jersey_number"]: # Missing information
            print(f"Skipped {name}: missing nation or number")
            continue

        player_dict[name] = {
            "team": player_data["team"],
            "number": int(player_data["tp_jersey_number"]),
            "nation": nation,
            "age": find_age(player_data["rawbirthdate"]),
            "conference": PWHL_TEAM_CONFERENCES[player_data["team"]]
        }

    # Add video players missing from rosters (e.g. camp invitees) using their saved data
    for name, player_data in PWHL_PLAYERS.items():
        if name not in player_dict:
            player_dict[name] = {
                "team": player_data["team"],
                "number": player_data["number"],
                "nation": player_data["nation"],
                "age": find_age(player_data["birthdate"]),
                "conference": player_data["conference"]
            }

    # Fetch existing cache from R2 after the API calls so fewer submitted results are overwritten
    cache_dictionary = load_cache(s3, bucket, PWHL_S3_CACHE_KEY)

    # Retrieve all players currently in the game
    existing_cached_players = cache_dictionary.get("players", {})

    # Add IDs for video players and results for everyone
    for name in player_dict:
        if name in PWHL_PLAYERS: # Only players with videos have IDs
            player_dict[name]["id"] = PWHL_PLAYERS[name]["id"]

        player_dict[name]["results"] = get_results(existing_cached_players, name, 6) # Fewer guesses for PWHL
    player_dict = dict(sorted(player_dict.items()))

    # Create video sources from players with both a video and an ID
    video_sources = {name: player_data["video"] for name, player_data in PWHL_PLAYERS.items() if "video" in player_data and "id" in player_data}

    # Only players with both a video and an ID can be daily answers
    eligible = list(video_sources)

    # Choose a new daily player, or keep the current one when only refreshing players
    if pick_daily or "daily_name" not in cache_dictionary:
        daily_name, unused_list, daily_history = pick_daily_player(cache_dictionary, eligible)
        updated = None
    else:
        daily_name, unused_list, daily_history = keep_daily_player(cache_dictionary)
        updated = cache_dictionary["updated"] # Keep the date so today's game stays locked for those who played

    save_cache(s3, bucket, PWHL_S3_CACHE_KEY, PWHL_LOCAL_CACHE_PATH, player_dict, video_sources, daily_name, unused_list, daily_history, updated)

def run_update(pick_daily=True):

    # Connect to Cloudflare R2
    s3 = boto3.client(
        service_name="s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    bucket = os.environ["R2_BUCKET_NAME"]

    # Update each league separately so one failing does not stop the other
    failed_leagues = []
    for league, update_league in (("NHL", update_nhl), ("PWHL", update_pwhl)):
        try:
            update_league(s3, bucket, pick_daily)
        except Exception: # Error handling
            print(f"Failed to update {league} player data:")
            traceback.print_exc()
            failed_leagues.append(league)

    # Mark the run as failed if any league failed
    if failed_leagues:
        raise RuntimeError(f"Update failed for: {', '.join(failed_leagues)}")

if __name__ == "__main__":
    run_update()
