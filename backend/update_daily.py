import os
import json
import boto3
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from nhl_api import get_player_info
from age_calculator import find_age
from random import choice
from data import TEAM_DIVISIONS_CONFERENCES, PLAYER_IDS, VIDEO_SOURCES
from pwhl_data import PWHL_PLAYERS, PWHL_EXTRAS
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
def get_results(existing_cached_players, name):
    return existing_cached_players.get(name, {}).get("results", {
        "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "X": 0, "total_guesses": 0
        })

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

# Save local copy and upload to Cloudflare R2
def save_cache(s3, bucket, key, local_path, player_dict, video_sources, daily_name, unused_list, daily_history):

    # Update file with new date and player dictionary
    est = ZoneInfo("America/New_York")
    new_cache = {
        "updated": datetime.now(tz=est).strftime("%Y-%m-%d"),
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

# Create and upload the NHL player data
def update_nhl(s3, bucket):

    # Fetch existing cache from R2
    cache_dictionary = load_cache(s3, bucket, NHL_S3_CACHE_KEY)

    # Retrieve all players currently in the game
    existing_cached_players = cache_dictionary.get("players", {})

    # Only players with both a video and an ID can be daily answers
    eligible = [name for name in VIDEO_SOURCES if name in PLAYER_IDS]

    # Retrieve data for all players
    all_player_data = get_player_info(list(PLAYER_IDS.values()))

    # Create formatted dictionary with player data
    player_dict = {
        name: {
            "team": player_data["currentTeamAbbrev"],
            "division": TEAM_DIVISIONS_CONFERENCES[player_data["currentTeamAbbrev"]][0],
            "number": player_data["sweaterNumber"],
            "nation": player_data["birthCountry"],
            "age": find_age(player_data["birthDate"]),
            "conference": TEAM_DIVISIONS_CONFERENCES[player_data["currentTeamAbbrev"]][1],
            "id": PLAYER_IDS[name],
            "results": get_results(existing_cached_players, name)
        }
        for name, player_data in zip(PLAYER_IDS.keys(), all_player_data)
    }

    daily_name, unused_list, daily_history = pick_daily_player(cache_dictionary, eligible)

    save_cache(s3, bucket, NHL_S3_CACHE_KEY, NHL_LOCAL_CACHE_PATH, player_dict, VIDEO_SOURCES, daily_name, unused_list, daily_history)

# Create and upload the PWHL player data
def update_pwhl(s3, bucket):

    # Fetch existing cache from R2
    cache_dictionary = load_cache(s3, bucket, PWHL_S3_CACHE_KEY)

    # Retrieve all players currently in the game
    existing_cached_players = cache_dictionary.get("players", {})

    # Combine players with and without videos, sorted by name
    all_players = dict(sorted({**PWHL_PLAYERS, **PWHL_EXTRAS}.items()))

    # Create formatted dictionary with player data
    player_dict = {}
    for name, player_data in all_players.items():
        player_dict[name] = {
            "team": player_data["team"],
            "number": player_data["number"],
            "nation": player_data["nation"],
            "age": find_age(player_data["birthdate"]),
            "conference": player_data["conference"]
        }

        if "id" in player_data: # Only players with videos have IDs
            player_dict[name]["id"] = player_data["id"]

        player_dict[name]["results"] = get_results(existing_cached_players, name)

    # Create video sources from players with both a video and an ID
    video_sources = {name: player_data["video"] for name, player_data in PWHL_PLAYERS.items() if "video" in player_data and "id" in player_data}

    # Only players with both a video and an ID can be daily answers
    eligible = list(video_sources)

    daily_name, unused_list, daily_history = pick_daily_player(cache_dictionary, eligible)

    save_cache(s3, bucket, PWHL_S3_CACHE_KEY, PWHL_LOCAL_CACHE_PATH, player_dict, video_sources, daily_name, unused_list, daily_history)

def run_update():

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
            update_league(s3, bucket)
        except Exception: # Error handling
            print(f"Failed to update {league} player data:")
            traceback.print_exc()
            failed_leagues.append(league)

    # Mark the run as failed if any league failed
    if failed_leagues:
        raise RuntimeError(f"Update failed for: {', '.join(failed_leagues)}")

if __name__ == "__main__":
    run_update()
