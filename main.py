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
    player_names = ["Connor McDavid", "Tim Stutzle", "Auston Matthews", "Leon Draisaitl"]

    # Form submission handling
    if request.method == "POST":
        player = request.form.get("player")
        return f"You submitted: {player}"

    # Render homepage w/ player names
    return render_template("index.html", players=player_names)

# Run the app
if __name__ == "__main__":
    app.run(debug=True) ### REMINDER: Change to False