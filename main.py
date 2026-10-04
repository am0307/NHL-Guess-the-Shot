import os, json
from flask import Flask, render_template, session
from flask_login import UserMixin, login_user, LoginManager, logout_user
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
from nhl_api import get_player_info
from age_calculator import find_age
from random import choice
from zoneinfo import ZoneInfo
from datetime import datetime
from dotenv import load_dotenv
from forms import RegisterForm

load_dotenv("secrets.env") # Load env file

# Initialise Flask and Bootstrap
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_KEY")
Bootstrap5(app)

csrf = CSRFProtect(app) # CSRF protection for forms

# Dictionary of NHL team abbreviations and their division/conference
TEAM_DIVISIONS_CONFERENCES = {"ANA": ("Pacific", "Western"), "BOS": ("Atlantic", "Eastern"), "BUF": ("Atlantic", "Eastern"),
                              "CGY": ("Pacific", "Western"), "CAR": ("Metro", "Eastern"), "CHI": ("Central", "Western"),
                              "COL": ("Central", "Western"), "CBJ": ("Metro", "Eastern"), "DAL": ("Central", "Western"),
                              "DET": ("Atlantic", "Eastern"), "EDM": ("Pacific", "Western"), "FLA": ("Atlantic", "Eastern"),
                              "LAK": ("Pacific", "Western"), "MIN": ("Central", "Western"), "MTL": ("Atlantic", "Eastern"),
                              "NSH": ("Central", "Western"), "NJD": ("Metro", "Eastern"), "NYI": ("Metro", "Eastern"),
                              "NYR": ("Metro", "Eastern"), "OTT": ("Atlantic", "Eastern"), "PHI": ("Metro", "Eastern"),
                              "PIT": ("Metro", "Eastern"), "SJS": ("Pacific", "Western"), "SEA": ("Pacific", "Western"),
                              "STL": ("Central", "Western"), "TBL": ("Atlantic", "Eastern"), "TOR": ("Atlantic", "Eastern"),
                              "UTA": ("Central", "Western"), "VAN": ("Pacific", "Western"), "VGK": ("Pacific", "Western"),
                              "WSH": ("Metro", "Eastern"), "WPG": ("Central", "Western")
                              }

# Players available to guess
PLAYER_IDS = {"Adam Fox":8479323, "Alex Ovechkin":8471214, "Auston Matthews":8479318, 
              "Cale Makar":8480069, "Cole Caufield":8481540, "Connor Bedard":8484144, 
              "Connor McDavid":8478402, "Cutter Gauthier":8483445, "David Pastrnak":8477956, 
              "Evan Bouchard":8480803, "Filip Forsberg":8476887, "Jack Eichel":8478403, 
              "Jack Hughes":8481559, "Jason Robertson":8480027, "Kirill Kaprizov":8478864, 
              "Kyle Connor":8478398, "Leon Draisaitl":8477934, "Linus Ullmark":8476999, 
              "Macklin Celebrini":8484801, "Matthew Schaefer":8485366, "Matthew Tkachuk":8479314, 
              "Matvei Michkov":8484387, "Mitch Marner":8478483, "Nathan MacKinnon":8477492, 
              "Nick Suzuki":8480018, "Nikita Kucherov":8476453, "Patrick Kane":8474141, 
              "Quinn Hughes":8480800, "Rasmus Dahlin":8480839, "Robert Thomas":8480023, 
              "Sebastian Aho":8478427, "Sidney Crosby":8471675, "Tage Thompson":8479420, 
              "Tim Stützle":8482116, "William Nylander":8477939, "Zach Werenski":8478460
              }

# Path to API cache file
CACHE_PATH = "api_cache.json"

# Retrieve API information from file, passing either full dictionary or daily player
def retrieve_API_info(desired_info):
    est = ZoneInfo("America/New_York") # To ignore user timezone
    today_est = datetime.now(tz=est).strftime("%Y-%m-%d")
    
    # In case cache file DNE
    cache_dictionary = {"unused_daily_players": []}
    
    if os.path.isfile(CACHE_PATH): # Verify file's existence
        
        # Open and verify file's currency
        with open(CACHE_PATH, "r", encoding="utf-8") as file: 
            cache_dictionary = json.load(file)
            if cache_dictionary["updated"] == today_est:
                return cache_dictionary[desired_info] # Return desired info if current
            
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
        for name, player_data in zip(PLAYER_IDS.keys(), all_player_data) # Use hard coded name spellings to avoid accents
    }
    
    # Check if unused daily players are in file
    if cache_dictionary["unused_daily_players"]:
        # Daily player to guess is randomly selected from players yet to be used
        daily_name = choice(cache_dictionary["unused_daily_players"])
        cache_dictionary["unused_daily_players"].remove(daily_name)
    else:
        # Daily player to guess is randomly selected from all players
        cache_dictionary["unused_daily_players"] = list(PLAYER_IDS.keys())
        daily_name = choice(list(PLAYER_IDS.keys()))
        cache_dictionary["unused_daily_players"].remove(daily_name)
            
    # Update file with new date and player dictionary
    with open(CACHE_PATH, "w", encoding="utf-8") as file: 
        json.dump({"updated": today_est, 
                   "players":player_dict, 
                   "unused_daily_players":cache_dictionary["unused_daily_players"],
                   "daily_name":daily_name}, file, ensure_ascii=False, indent=4)     
    
    if desired_info == "daily_name":
        return daily_name
    else:
        return player_dict    

# Homepage route
@app.route("/", methods=["GET", "POST"])
def home():
    
    daily_name = retrieve_API_info("daily_name") # Retrieve daily name
    player_dict = retrieve_API_info("players") # Retrieve player dictionary
    
    # Check and, if necessary, create an unused players list to avoid repeats
    if "players_to_use" not in session or not session["players_to_use"]: # Checks if list DNE or ran out of players
        session["players_to_use"] = list(PLAYER_IDS.keys())
    
    # Player to guess is randomly selected from players yet to be used
    daily_info = player_dict[daily_name]
    
    if daily_name in session["players_to_use"]: # Safety check
        session["players_to_use"].remove(daily_name) # Remove player from unused list
    
    session.modified = True # Force Flask to save change to unused list
            
    # Render homepage w/ player names
    return render_template("index.html", 
                           players=list(PLAYER_IDS.keys()), 
                           player_data=player_dict, 
                           answer_info=daily_info, 
                           answer_name=daily_name,
                           players_to_use=session["players_to_use"])

# Endless mode route
@app.route("/endless", methods=["GET", "POST"])
def endless_mode():
    
    player_dict = retrieve_API_info("players") # Retrieve player dictionary
    
    # Check and, if necessary, create an unused players list to avoid repeats
    if "players_to_use" not in session or not session["players_to_use"]: # Checks if list DNE or ran out of players
        session["players_to_use"] = list(PLAYER_IDS.keys())
    
    # Player to guess is randomly selected from players yet to be used
    answer_name = choice(session["players_to_use"])
    answer_info = player_dict[answer_name]
    
    if answer_name in session["players_to_use"]: # Safety check
        session["players_to_use"].remove(answer_name) # Remove player from unused list
    
    session.modified = True # Force Flask to save change to unused list
            
    # Render homepage w/ player names
    return render_template("endless.html", 
                           players=list(PLAYER_IDS.keys()), 
                           player_data=player_dict, 
                           answer_info=answer_info, 
                           answer_name=answer_name,
                           players_to_use=session["players_to_use"])

# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    return render_template("register.html", form=form)    

# Run the app
if __name__ == "__main__":
    app.run(debug=True) ### REMINDER: Change to False