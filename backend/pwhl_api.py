import requests
import time

# PWHL HockeyTech feed and its public parameters
PWHL_FEED_URL = "https://lscluster.hockeytech.com/feed/index.php"
PWHL_FEED_PARAMS = {"feed": "modulekit", "key": "446521baf8c38984", "client_code": "pwhl"}

# Retrieves a view from the feed, retrying if an error page is returned instead of JSON
def get_feed(session, view, attempts=3, **params):
    for attempt in range(attempts):
        response = session.get(url=PWHL_FEED_URL, params={**PWHL_FEED_PARAMS, "view": view, **params})
        response.raise_for_status()

        time.sleep(0.5) # Avoid rate limiting

        try:
            return response.json()["SiteKit"]
        except requests.exceptions.JSONDecodeError:
            if attempt == attempts - 1: # Out of attempts
                raise

# Retrieves every rostered player for each team, keyed by ID
def get_pwhl_rosters():

    with requests.Session() as session: # Session for more efficient requests

        session.headers.update({"User-Agent": "PWHL PuckGuessr Game"}) # Identifying header

        # Retrieve the two newest non-playoff seasons
        seasons = [season["season_id"] for season in get_feed(session, "seasons")["Seasons"] if season["playoff"] == "0"][:2]

        # Use the newest season with players (e.g. pre-season until regular season rosters are set)
        for season_id in seasons:
            data = {}

            # Loop through teams to receive forwards, defence, and goalies
            for team in get_feed(session, "teamsbyseason", season_id=season_id)["Teamsbyseason"]:
                for player in get_feed(session, "roster", team_id=team["id"], season_id=season_id)["Roster"]:
                    if isinstance(player, dict): # Skip empty entries at the end of each roster
                        data[player["player_id"]] = {**player, "team": team["code"]}

            if data:
                return data

    return {}
