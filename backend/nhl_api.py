import requests
import time

# Retrieves detailed player information using the player IDs
def get_player_info(player_ids):
    
    data = []
    
    with requests.Session() as session: # Session for more efficient requests
        
        session.headers.update({"User-Agent": "NHL PuckGuessr Game"}) # Identifying header
        
        # Loop through IDs to receive data from all players
        for player_id in player_ids:
            url = f"https://api-web.nhle.com/v1/player/{player_id}/landing"

            response = session.get(url=url)
            response.raise_for_status()
            data.append(response.json())
        
            time.sleep(0.5) # Avoid rate limiting

    return data

# Retrieves every rostered player for each team, keyed by ID
def get_team_rosters(teams):

    data = {}

    with requests.Session() as session: # Session for more efficient requests

        session.headers.update({"User-Agent": "NHL PuckGuessr Game"}) # Identifying header

        # Loop through teams to receive forwards, defencemen, and goalies
        for team in teams:
            url = f"https://api-web.nhle.com/v1/roster/{team}/current"

            response = session.get(url=url)
            response.raise_for_status()

            for position_group in response.json().values():
                for player in position_group:
                    data[player["id"]] = {**player, "team": team}

            time.sleep(0.5) # Avoid rate limiting

    return data