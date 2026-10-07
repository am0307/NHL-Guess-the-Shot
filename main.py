import os, json
from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
from nhl_api import get_player_info
from age_calculator import find_age
from random import choice
from zoneinfo import ZoneInfo
from datetime import datetime
from dotenv import load_dotenv
from data import TEAM_DIVISIONS_CONFERENCES, PLAYER_IDS, VIDEO_SOURCES

load_dotenv("secrets.env") # Load env file

# Initialise Flask and Bootstrap
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_KEY")
Bootstrap5(app)

# Set session cookie security settings
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

csrf = CSRFProtect(app) # CSRF protection for forms

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
    
    daily_info = player_dict[daily_name] # Player to guess is randomly selected from players yet to be used
    
    daily_id = daily_info["id"]  # Get the ID of the daily player
    
    # Check if they have already played this player
    already_played = daily_name not in session["players_to_use"]
    
    # Render homepage w/ player names
    return render_template("index.html", 
                           players=list(PLAYER_IDS.keys()), 
                           player_data=player_dict, 
                           answer_id=daily_id,
                           players_to_use=session["players_to_use"],
                           video_sources=VIDEO_SOURCES,
                           already_played=already_played)

# Endless mode route
@app.route("/endless", defaults={"player_id": None}, methods=["GET", "POST"])
@app.route("/endless/<int:player_id>", methods=["GET", "POST"])
def endless_mode(player_id):
    
    player_dict = retrieve_API_info("players") # Retrieve player dictionary
    
    # Check and, if necessary, create an unused players list to avoid repeats
    if "players_to_use" not in session or not session["players_to_use"]: # Checks if list DNE or ran out of players
        session["players_to_use"] = list(PLAYER_IDS.keys())
    
    # If no player_id is provided in the url, generate one and redirect
    if player_id is None:
        answer_name = choice(session["players_to_use"])
        new_player_id = player_dict[answer_name]["id"]
        return redirect(url_for('endless_mode', player_id=new_player_id))
    
    # If a player_id is provided, find the matching player
    answer_name = None
    for name, info in player_dict.items():
        if info["id"] == player_id:
            answer_name = name
            break
        
    # Fallback if user types an invalid player_id themselves
    if not answer_name:
        return redirect(url_for('endless_mode'))
    
    answer_info = player_dict[answer_name]
    answer_id = answer_info["id"]  # Get the ID of the selected player
    
    # Determine if player has already been played
    already_played = answer_name not in session["players_to_use"]
    
    # Render homepage w/ player names
    return render_template("endless.html", 
                           players=list(PLAYER_IDS.keys()), 
                           player_data=player_dict, 
                           answer_id=answer_id,
                           players_to_use=session["players_to_use"],
                           video_sources=VIDEO_SOURCES,
                           already_played=already_played,
                           endless_streak=session.get("endless_streak", 0))

# Update endless streaks
@app.route("/update_endless_streak", methods=["POST"])
def update_endless_streak():
    
    # Retrieve data
    data = request.get_json()
    result = data.get("result")
    player_id = data.get("player_id")
    mode = data.get("mode")

    # Mark player as used when the user actually completes the round
    if player_id is not None:
        player_dict = retrieve_API_info("players")
        player_name = next((name for name, info in player_dict.items() if info["id"] == player_id), None) # Find player name
        
        # Remove player from unused list if needed
        if player_name and player_name in session.get("players_to_use", []):
            session["players_to_use"].remove(player_name)

    # Initialise streak if necessary
    if "endless_streak" not in session:
        session["endless_streak"] = 0

    # Only update the streak counter when user is in endless mode
    if mode == "endless":
        if result == "win":
            session["endless_streak"] += 1
        elif result == "loss":
            session["endless_streak"] = 0
        
    session.modified = True # Force Flask to save change to streak

    return jsonify({"streak": session["endless_streak"]})

# Run the app
if __name__ == "__main__":
    app.run(debug=True) ### REMINDER: Change to False