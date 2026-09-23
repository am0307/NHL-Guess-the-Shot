import os
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap5

# Initialise Flask and Bootstrap
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")
Bootstrap5(app)

# Homepage route
@app.route("/", methods=["GET", "POST"])
def home():

    # Hard coded list of players for testing
    player_dict = [{"Connor McDavid": {
                        "team": "Edmonton Oilers", "division": "Pacific", "number": 97, "nation": "Canada", "age": 29
                        }}, 
                   {"Tim Stutzle": {
                        "team": "Washington Capitals", "division": "Metropolitan", "number": 21, "nation": "Canada", "age": 24
                        }}, 
                   {"Auston Matthews": {
                       "team": "Toronto Maple Leafs", "division": "Atlantic", "number": 14, "nation": "USA", "age": 29
                       }}, 
                   {"Leon Draisaitl": {
                       "team": "Edmonton Oilers", "division": "Pacific", "number": 29, "nation": "Germany", "age": 30
                       }}]

    # Form submission handling
    if request.method == "POST":
        input_name = request.form.get("player")
        return f"You submitted: {input_name}"

    player_names = [list(player.keys())[0] for player in player_dict]
        
    # Render homepage w/ player names
    return render_template("index.html", players=player_names)

# Run the app
if __name__ == "__main__":
    app.run(debug=True) ### REMINDER: Change to False