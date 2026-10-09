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

load_dotenv("secrets.env")

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
    cache_path = "api_cache.json"

    # Fetch existing cache from R2
    cache_dictionary = {"unused_daily_players": []}
    try:
        response = s3.get_object(Bucket=bucket, Key=cache_path)
        cache_dictionary = json.loads(response['Body'].read().decode('utf-8'))
    except Exception:
        pass # Triggers if the file DNE

    # If file DNE or is not current, get new data
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
            "id": PLAYER_IDS[name]
        }
        for name, player_data in zip(PLAYER_IDS.keys(), all_player_data)
    }
    
    # Select daily player
    if cache_dictionary.get("unused_daily_players"): # Unused player list exists
        # Daily player to guess is randomly selected from players yet to be used
        daily_name = choice(cache_dictionary["unused_daily_players"])
    else:
        # Daily player to guess is randomly selected from all players
        cache_dictionary["unused_daily_players"] = list(PLAYER_IDS.keys())
        daily_name = choice(list(PLAYER_IDS.keys()))
        
    cache_dictionary["unused_daily_players"].remove(daily_name) # Remove new daily player name

    # Update file with new date and player dictionary
    est = ZoneInfo("America/New_York")
    new_cache = {
        "updated": datetime.now(tz=est).strftime("%Y-%m-%d"), 
        "players": player_dict, 
        "unused_daily_players": cache_dictionary["unused_daily_players"],
        "daily_name": daily_name,
        "video_sources": VIDEO_SOURCES
    }

    # Prepare JSON data
    json_data = json.dumps(new_cache, ensure_ascii=False, indent=4)

    # Save local copy
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(json_data)
        
    # Upload to Cloudflare R2
    s3.put_object(
        Bucket=bucket,
        Key=cache_path,
        Body=json.dumps(new_cache, ensure_ascii=False, indent=4),
        ContentType="application/json"
    )

if __name__ == "__main__":
    run_update()