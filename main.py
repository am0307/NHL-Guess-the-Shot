import os, json, jsonify
from unittest import result
from flask import Flask, render_template, session, flash, redirect, url_for, request
from flask_login import UserMixin, login_user, LoginManager, logout_user, current_user, login_required
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from nhl_api import get_player_info
from age_calculator import find_age
from random import choice
from zoneinfo import ZoneInfo
from datetime import datetime
from dotenv import load_dotenv
from forms import RegisterForm, LoginForm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv("secrets.env") # Load env file

# Initialise Flask and Bootstrap
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_KEY")
Bootstrap5(app)

# Initialise Flask limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=["1000 per day", "500 per hour"] 
)

# Set session cookie security settings
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Configure Flask login
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

csrf = CSRFProtect(app) # CSRF protection for forms

# Create database
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URI", "sqlite:///users.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create user model
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    daily_streak: Mapped[int] = mapped_column(Integer, default=0)
    endless_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_daily_date: Mapped[str] = mapped_column(String(15), nullable=True) 
    last_daily_status: Mapped[str] = mapped_column(String(10), nullable=True)

# Create database
with app.app_context():
    db.create_all()
    
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
            
    # Check if user already played today
    daily_completed = False
    if current_user.is_authenticated:
        est = ZoneInfo("America/New_York")
        today_est = datetime.now(tz=est).strftime("%Y-%m-%d")
        if current_user.last_daily_date == today_est:
            daily_completed = True
    
    daily_id = daily_info["id"]  # Get the ID of the daily player
    
    # Render homepage w/ player names
    return render_template("index.html", 
                           players=list(PLAYER_IDS.keys()), 
                           player_data=player_dict, 
                           answer_id=daily_id,
                           players_to_use=session["players_to_use"],
                           daily_completed=daily_completed)

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
    answer_id = answer_info["id"]  # Get the ID of the selected player
    
    if answer_name in session["players_to_use"]: # Safety check
        session["players_to_use"].remove(answer_name) # Remove player from unused list
    
    session.modified = True # Force Flask to save change to unused list
            
    # Render homepage w/ player names
    return render_template("endless.html", 
                           players=list(PLAYER_IDS.keys()), 
                           player_data=player_dict, 
                           answer_id=answer_id,
                           players_to_use=session["players_to_use"])

# Register route
@app.route("/register", methods=["GET", "POST"])
@limiter.limit("50 per minute")
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data

        matching_user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        
        if matching_user != None:
            flash("You've already signed up with that email, try logging in instead!")
            return redirect(url_for("login"))
        elif form.password.data != form.verify_password.data:
            flash("Passwords do not match, please try again.")
            return redirect(url_for("register"))
        
        plain_password = form.password.data
        encrypted_password = generate_password_hash(password=plain_password, method="pbkdf2:sha256", salt_length=8)

        new_user = User(email=email, password=encrypted_password)

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect(url_for("home"))
    
    return render_template("register.html", form=form)    

# Login route
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("50 per minute")
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        plain_password = form.password.data
        
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()

        if user != None:
            password_check = check_password_hash(pwhash=user.password, password=plain_password)

            if password_check:
                login_user(user)
                return redirect(url_for("home"))
            else:
                flash("Incorrect password, please try again.")
                return render_template("login.html", form=form)
        else:
            flash("That email does not exist, please try again.")
            return redirect(url_for("login", form=form))
    
    return render_template("login.html", form=form)

# Logout route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

# Error handler for rate limiting
@app.errorhandler(429)
def ratelimit_handler(e):
    flash("Too many login attempts. Please try again in a minute.")
    return redirect(url_for("login"))

# Update streak route
@app.route("/update_streak", methods=["POST"])
@login_required
def update_streak():
    
    # Get JSON data from request
    data = request.get_json()
    mode = data.get("mode")
    result = data.get("result")
    
    # Get current date in EST
    est = ZoneInfo("America/New_York")
    today_est = datetime.now(tz=est).strftime("%Y-%m-%d")

    # Update streak based on mode and result
    if mode == "daily":
        # Update daily streak only if the user hasn't played today
        if current_user.last_daily_date == today_est:
            return jsonify({"success": False, "message": "Already played today."}), 400
            
        current_user.last_daily_date = today_est
        current_user.last_daily_status = result
        
        if result == "win":
            current_user.daily_streak += 1
        else:
            current_user.daily_streak = 0
            
        db.session.commit()
        return jsonify({"streak": current_user.daily_streak})
    elif mode == "endless":
        if result == "win":
            current_user.endless_streak += 1
        else:
            current_user.endless_streak = 0
            
        db.session.commit()
        return jsonify({"streak": current_user.endless_streak})
        
    return jsonify({"success": False}), 400

# Run the app
if __name__ == "__main__":
    app.run(debug=True) ### REMINDER: Change to False