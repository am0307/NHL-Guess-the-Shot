import os, json
from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5
from nhl_api import get_player_info
from age_calculator import find_age
from random import choice
from zoneinfo import ZoneInfo
from datetime import datetime

# Initialise Flask and Bootstrap
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")
Bootstrap5(app)

# Dictionary of NHL team abbreviations and their division/conference
TEAM_DIVISIONS_CONFERENCES = {"ANA": ("Pacific", "Western"), "BOS": ("Atlantic", "Eastern"), "BUF": ("Atlantic", "Eastern"),
                              "CGY": ("Pacific", "Western"), "CAR": ("Metropolitan", "Eastern"), "CHI": ("Central", "Western"),
                              "COL": ("Central", "Western"), "CBJ": ("Metropolitan", "Eastern"), "DAL": ("Central", "Western"),
                              "DET": ("Atlantic", "Eastern"), "EDM": ("Pacific", "Western"), "FLA": ("Atlantic", "Eastern"),
                              "LAK": ("Pacific", "Western"), "MIN": ("Central", "Western"), "MTL": ("Atlantic", "Eastern"),
                              "NSH": ("Central", "Western"), "NJD": ("Metropolitan", "Eastern"), "NYI": ("Metropolitan", "Eastern"),
                              "NYR": ("Metropolitan", "Eastern"), "OTT": ("Atlantic", "Eastern"), "PHI": ("Metropolitan", "Eastern"),
                              "PIT": ("Metropolitan", "Eastern"), "SJS": ("Pacific", "Western"), "SEA": ("Pacific", "Western"),
                              "STL": ("Central", "Western"), "TBL": ("Atlantic", "Eastern"), "TOR": ("Atlantic", "Eastern"),
                              "UTA": ("Central", "Western"), "VAN": ("Pacific", "Western"), "VGK": ("Pacific", "Western"),
                              "WSH": ("Metropolitan", "Eastern"), "WPG": ("Central", "Western")
                              }

# Players available to guess
PLAYER_IDS = {"Alex Ovechkin":8471214, "Auston Matthews":8479318, "Cole Caufield":8481540, 
              "Connor Bedard":8484144, "Connor McDavid":8478402, "David Pastrnak":8477956, 
              "Evan Bouchard":8480803, "Jason Robertson":8480027, "Kirill Kaprizov":8478864, 
              "Leon Draisaitl":8477934, "Linus Ullmark":8476999, "Macklin Celebrini":8484801, 
              "Matthew Tkachuk":8479314, "Mitch Marner":8478483, "Nathan MacKinnon":8477492,
              "Patrick Kane":8474141, "Sidney Crosby":8471675, "Tage Thompson":8479420, 
              "Tim Stutzle":8482116, "William Nylander":8477939
              }

# Path to API cache file
CACHE_PATH = "api_cache.json"

# Retrieve the player dictionary, either by refreshing from API or from cached file
def retrieve_player_dict():
    est = ZoneInfo("America/New_York") # To ignore user timezone
    today_est = datetime.now(tz=est).strftime("%Y-%m-%d")
    
    if os.path.isfile(CACHE_PATH): # Verify file's existence
        
        # Open and verify file's currency
        with open(CACHE_PATH, "r", encoding="utf-8") as file: 
            cache_dictionary = json.load(file)
            if cache_dictionary["updated"] == today_est:
                return cache_dictionary["players"] # Return dictionary if current
            
    # If file DNE or is not current, get new data
    all_player_data = get_player_info(list(PLAYER_IDS.values()))
    
    # Create formatted dictionary with player data
    player_dict = {
        name: {
            "team": player_data["teamCommonName"]["default"],
            "division": TEAM_DIVISIONS_CONFERENCES[player_data["currentTeamAbbrev"]][0],
            "number": player_data["sweaterNumber"],
            "nation": player_data["birthCountry"],
            "age": find_age(player_data["birthDate"]),
            "conference": TEAM_DIVISIONS_CONFERENCES[player_data["currentTeamAbbrev"]][1],
        }
        for name, player_data in zip(PLAYER_IDS.keys(), all_player_data) # Use hard coded name spellings to avoid accents
    }
    
    # Update file with new date and player dictionary
    with open(CACHE_PATH, "w", encoding="utf-8") as file: 
        json.dump({"updated": today_est, "players":player_dict}, file, ensure_ascii=False)
    
    return player_dict


# Homepage route
@app.route("/", methods=["GET", "POST"])
def home():
                               
    player_dict = retrieve_player_dict() # Retrieve player dictionary
    
    # Player to guess is randomly selected
    answer_name = choice(list(PLAYER_IDS.keys()))
    answer_info = player_dict[answer_name]
            
    # Render homepage w/ player names
    return render_template("index.html", 
                           players=list(PLAYER_IDS.keys()), 
                           player_data=player_dict, 
                           answer_info=answer_info, 
                           answer_name=answer_name)

# Run the app
if __name__ == "__main__":
    app.run(debug=True) ### REMINDER: Change to False