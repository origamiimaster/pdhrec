"""
Runs the flask server to host the project...
Not for deployment, just development for now
"""
from flask import Flask
from azure_database import new_get_all_commander_counts, get_new_synergy_scores
import json

app = Flask(__name__, static_url_path="")


@app.route('/commander/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return json.dumps(get_new_synergy_scores(username))


@app.route("/top-commanders")
def top_commanders():
    return json.dumps(new_get_all_commander_counts())


@app.route("/")
def hello():
    return "<html><body> TESTING.... go to /topcommanders</body></html>"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)  # run our Flask app
