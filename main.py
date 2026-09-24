import os
from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5

# Initialise Flask and Bootstrap
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")
Bootstrap5(app)

# Homepage route
@app.route("/", methods=["GET", "POST"])
def home():

    # Hard coded dictionary of players for testing
    player_dict = {"Connor McDavid": {"team": "Oilers", "division": "Pacific", "number": 97, "nation": "Canada", "age": 29},
                   "Tim Stutzle": {"team": "Senators", "division": "Atlantic", "number": 18, "nation": "Germany", "age": 24},
                   "Auston Matthews": {"team": "Maple Leafs", "division": "Atlantic", "number": 34, "nation": "USA", "age": 29},
                   "Leon Draisaitl": {"team": "Oilers", "division": "Pacific", "number": 29, "nation": "Germany", "age": 30}
}
    player_names = list(player_dict.keys())
        
    # Render homepage w/ player names
    return render_template("index.html", players=player_names, player_data=player_dict)

# Run the app
if __name__ == "__main__":
    app.run(debug=True) ### REMINDER: Change to False