"""
Runs the flask server to host the project...
Not for deployment, just development for now
"""
from flask import Flask, send_file, request
from azure_database import new_get_all_commander_counts, get_new_synergy_scores
import json

app = Flask(__name__, static_url_path="")


@app.route('/commander/<name>')
def show_commander(name):
    if "format" in request.args:
        format = request.args.get("format")
        if format == "json":
            return json.dumps(get_new_synergy_scores(name))
    return get_pretty_commander(get_new_synergy_scores(name))


def get_pretty_commander(commander_data):
    cards_and_scores = [(card, commander_data[card]) for card in commander_data]
    cards_and_scores.sort(key=lambda x: x[1])
    cards_and_scores.reverse()
    cards_and_scores_text = [x[0] + ":" + str(x[1]) for x in cards_and_scores]
    return f"""
<html>
    <head>
    </head>
<body>
{'<br>'.join(cards_and_scores_text)}
</body>
</html>
"""


@app.route('/commander/')
def blank():
    return json.dumps({})


@app.route("/top-commanders")
def top_commanders():
    return json.dumps(new_get_all_commander_counts())


@app.route("/")
def hello():
    return send_file("static/index.html")


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)  # run our Flask app
