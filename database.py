"""
Store and load data saved by the project.

Three main collections will be use: 
1. Deck metadata. Has deck been updated? Other details...
2. Deck Cards: For each deck, what cards does it run? Is it legal?
3. Commander Cards: For each commander, what cards does it run? In what quantities?
"""
from pymongo import MongoClient
import datetime
from dateutil import parser
client = MongoClient()
db = client['pdhrec']


def save_metadata(data):
    """
    Inserts deck metadata into the metadata collection, updating if exists already, otherwise inserting.
    :param data: deck metadata, a dict of publicId, id, lastUpdatedAtUtc, name, hasPrimer, needsUpdate.
    :return: None
    """
    # print(data)
    col = db['metadata']
    data["_id"] = data['publicId']
    data['lastUpdatedAtUtc'] = parser.parse(data['lastUpdatedAtUtc']).timestamp()
    data["needsUpdate"] = True
    col.update_one({"_id": data["_id"]}, {"$set": data}, upsert=True)


def load_metadata(publicId):
    return db['metadata'].find_one({"_id": publicId})


def save_cards(data):
    col = db['decks']
    info = {'_id': data['publicId'], 'cards': {}, 'commanders': {}}
    for card in data['mainboard']:
        if data['mainboard'][card]['card']['legalities']['paupercommander'] != "legal":
            return False
        info['cards'][card] = data['mainboard'][card]["quantity"]

    # print(info)
    for card in data['commanders']:
        info['commanders'][card] = data['commanders'][card]['quantity']
        if data['commanders'][card]['card']['legalities']['paupercommander'] == "restricted":
            pass
        elif data['commanders'][card]['card']['legalities']['paupercommander'] == "legal":
            if data['commanders'][card]['card']['rarity'] == "uncommon" and data['commanders'][card]['card'][
                'type'] == "2":
                pass
            else:
                return False
        else:
            return False
    mainboard = 0
    for card in info['cards']:
        mainboard += info['cards'][card]
    for card in info['commanders']:
        mainboard += info['commanders'][card]
    if mainboard != 100:
        return False
    print("Inserting cards..")
    col.update_one({'_id': info['_id']}, {"$set": info}, upsert=True)
    return True


def load_cards(publicId):
    pass


# def insert_new_commander_data(data):
#     pass
#
# def update_commander_data(old_data, new_data):
#     pass

def get_ids_need_update():
    col = db['metadata']
    return [x['_id'] for x in col.find({"needsUpdate": True})]

def get_newest_metadata():
    col = db['metadata']
    col.find_one()
    return [x for x in db['metadata'].find().sort("lastUpdatedAtUtc", -1).limit(1)][0]

def get_all_metadata():
    return db['metadata'].find({})

def get_commander_aggregate():
    col = db['decks']
    result = col.aggregate()
    print(result)


if __name__ == "__main__":
    save_metadata({"publicId": "0"})
