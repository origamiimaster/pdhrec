"""
Runs the flask server to host the project...
Not for deployment, just development for now
"""
from flask import Flask, send_file, request, redirect
from urllib.parse import quote, unquote

from utils import normalize_text
# import database
from azure_database import get_all_staples, new_get_all_commander_counts, get_new_synergy_scores, \
    check_commander_exists, \
    get_commander_names, get_commander_data, add_website_visit, get_website_visit, retrieve_card_image
import json

app = Flask(__name__, static_url_path="")


@app.route('/commander/<name>')
def show_commander(name):
    if "format" in request.args:
        format = request.args.get("format")
        if format == "json":
            return json.dumps({"cards": get_new_synergy_scores(name), "commander": get_commander_data(name)})
    # Return the deck data page...
    return send_file("static/data.html")


def get_pretty_commander(commander_data):
    cards_and_scores = [(card, commander_data[card]) for card in commander_data]
    cards_and_scores.sort(key=lambda x: x[1])
    cards_and_scores.reverse()
    # cards_and_scores_text = [x[0] + ":" + str(x[1]) for x in cards_and_scores]
    cards_and_scores_text = [f"<tr><td>{x[0]}</td><td>{'{0:.2%}'.format(x[1])}</td></tr>" for x in cards_and_scores]
    return f"""
<html>
    <head>
        <!-- <link rel="stylesheet" href="main.css"></link>-->
        <style>
            table {{
                border-color: blue;
                width: 100%;
                font-size: 1.5em;
            }}

        </style>
    </head>
<body>
<h1> Card Data (beta) </h1>
<table>
<tr><th>Card Name</th><th>Synergy Score</th></tr>
{''.join(cards_and_scores_text)}
</table>
</body>
</html>
"""


@app.route('/commander/')
def blank():
    return json.dumps({})


@app.route("/top-commanders")
def top_commanders():
    return json.dumps(new_get_all_commander_counts())


@app.route("/commander-names")
def commander_names():
    return json.dumps([x for x in get_commander_names()])


@app.route("/")
def hello():
    return send_file("static/index.html")


@app.route("/get-staples")
def get_staples():
    return json.dumps(get_all_staples())


@app.route("/staples")
def staples():
    return send_file("static/staples.html")


@app.route("/counter")
def counter():
    return {"count": get_website_visit()}


@app.route("/add-site-counter")
def add_site_counter():
    add_website_visit()
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route("/image/<name>")
def image(name):
    return retrieve_card_image(unquote(name))


@app.route("/search")
def search():
    if "q" in request.args:
        query = request.args.get("q")
        print(query)
        try:
            clean_name = normalize_text([query])[0]
            print(clean_name)
            print(check_commander_exists(clean_name))
            if check_commander_exists(clean_name):
                return redirect("commander/" + clean_name)
            else:
                return redirect("/")
            # return json.dumps(get_new_synergy_scores(normalize_text(query)))
        except Exception as e:
            return json.dumps({str(e)})
    else:
        return json.dumps({})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)  # run our Flask app
