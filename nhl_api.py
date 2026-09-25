import requests
import time

# Retrieves detailed player information using the player IDs
def get_player_info(player_ids):
    
    data = []
    
    with requests.Session() as session: # Session for more efficient requests
        
        session.headers.update({"User-Agent": "NHL Guess the Shot Game"}) # Identifying header
        
        # Loop through IDs to receive data from all playhers
        for player_id in player_ids:
            url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"

            response = requests.get(url=url)
            response.raise_for_status()
            data.append(response.json())
        
            time.sleep(0.5) # Avoid rate limiting
    
    return data