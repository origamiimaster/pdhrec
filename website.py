"""
Runs the flask server to host the project...
Not for deployment, just development for now
"""
from flask import Flask, url_for, escape
from database import new_get_all_commander_counts, get_synergy_scores, get_new_synergy_scores
import json

app = Flask(__name__)

@app.route('/commander/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return json.dumps(get_new_synergy_scores(username))

@app.route("/top-commanders")
def top_commanders():
    return json.dumps(new_get_all_commander_counts())
