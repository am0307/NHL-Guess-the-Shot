import requests, urllib.parse
import time

# Retrieves detailed player information using the player's ID
def get_player_info(player_id):
    url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"

    response = requests.get(url=url)
    response.raise_for_status()
    data = response.json()
    
    time.sleep(0.5) # Avoid rate limiting
    
    return data