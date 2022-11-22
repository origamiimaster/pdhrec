from flask import Flask
from flask_restful import Resource, Api, reqparse
from database import new_get_all_commander_counts
app = Flask(__name__)
api = Api(app)


class TopCommanders(Resource):
    def get(self):
        return {'data': new_get_all_commander_counts()}, 200

api.add_resource(TopCommanders, "/topcommanders")


class Commanders(Resource):
    def get(self):
        return {'data': []}, 200


api.add_resource(Commanders, "/commander")


@app.route("/")
def hello():
    return "<p>Hello World</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # run our Flask app
