import os
import json
import boto3
from datetime import datetime
from zoneinfo import ZoneInfo
from nhl_api import get_player_info
from age_calculator import find_age
from random import choice
from data import TEAM_DIVISIONS_CONFERENCES, PLAYER_IDS, VIDEO_SOURCES
from dotenv import load_dotenv
from pathlib import Path

# Load secrets.env from the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / "secrets.env"
load_dotenv(dotenv_path=ENV_PATH)

# Local path for writing the file
LOCAL_CACHE_PATH = ROOT_DIR / "player_data.json"

# Bucket key
S3_CACHE_KEY = "player_data.json"

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

    # Fetch existing cache from R2
    cache_dictionary = {"unused_daily_players": []}
    try:
        response = s3.get_object(Bucket=bucket, Key=S3_CACHE_KEY)
        cache_dictionary = json.loads(response['Body'].read().decode('utf-8'))
    except Exception:
        pass # Triggers if the file DNE

    # Retrieve daily history
    daily_history = cache_dictionary.get("daily_history", {})
    
    # Retrieve all players currently in the game
    existing_cached_players = cache_dictionary.get("players", {})
    
    # Only players with both a video and an ID can be daily answers
    eligible = [name for name in VIDEO_SOURCES if name in PLAYER_IDS]

    # Keep only eligible names from the saved list
    unused_list = [n for n in cache_dictionary.get("unused_daily_players", []) if n in eligible]

    # Add video players who have not yet been a daily answer
    used_names = set(daily_history.values())
    for name in eligible:
        if name not in used_names and name not in unused_list:
            unused_list.append(name)

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
            "results": existing_cached_players.get(name, {}).get("results", {
                "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "X": 0, "total_guesses": 0
                })
        }
        for name, player_data in zip(PLAYER_IDS.keys(), all_player_data)
    }
    
    # Refill from eligible players only, avoiding an immediate repeat of yesterday's answer
    if not unused_list:
        last_daily = daily_history.get(str(len(daily_history)))
        unused_list = [n for n in eligible if n != last_daily] or eligible

    daily_name = choice(unused_list)
    unused_list.remove(daily_name)
    cache_dictionary["unused_daily_players"] = unused_list

    # Append the new daily player to the daily history
    next_index = str(len(daily_history) + 1)
    daily_history[next_index] = daily_name
    
    # Update file with new date and player dictionary
    est = ZoneInfo("America/New_York")
    new_cache = {
        "updated": datetime.now(tz=est).strftime("%Y-%m-%d"), 
        "players": player_dict, 
        "unused_daily_players": cache_dictionary["unused_daily_players"],
        "daily_name": daily_name,
        "daily_history": daily_history,
        "video_sources": VIDEO_SOURCES
    }

    # Prepare JSON data
    json_data = json.dumps(new_cache, ensure_ascii=False, indent=4)

    # Save local copy
    with open(LOCAL_CACHE_PATH, "w", encoding="utf-8") as f:
        f.write(json_data)
        
    # Upload to Cloudflare R2
    s3.put_object(
        Bucket=bucket,
        Key=S3_CACHE_KEY,
        Body=json.dumps(json_data, ensure_ascii=False, indent=4),
        ContentType="application/json",
        CacheControl="no-cache, no-store, must-revalidate"
    )

if __name__ == "__main__":
    run_update()