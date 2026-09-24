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
    player_dict = {"Connor McDavid": {"team": "Oilers", "division": "Pacific", "number": 97, "nation": "Canada", "age": 29, "conference": "Western"},
                   "Tim Stutzle": {"team": "Senators", "division": "Atlantic", "number": 18, "nation": "Germany", "age": 24, "conference": "Eastern"},
                   "Auston Matthews": {"team": "Maple Leafs", "division": "Atlantic", "number": 34, "nation": "USA", "age": 29, "conference": "Eastern"},
                   "Leon Draisaitl": {"team": "Oilers", "division": "Pacific", "number": 29, "nation": "Germany", "age": 30, "conference": "Western"},
                   "Zach Hyman": {"team": "Oilers", "division": "Pacific", "number": 18, "nation": "Canada", "age": 34, "conference": "Western"}
                   }
                   
    player_names = list(player_dict.keys())
    
    # Hard coded player to guess for testing
    answer_name = "Zach Hyman"
    answer_info = player_dict[answer_name]
    
    print(answer_info)
        
    # Render homepage w/ player names
    return render_template("index.html", players=player_names, player_data=player_dict, answer_info=answer_info, answer_name=answer_name)

# Run the app
if __name__ == "__main__":
    app.run(debug=True) ### REMINDER: Change to False