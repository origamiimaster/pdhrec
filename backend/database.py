"""
Store and load data saved by the project.

Three main collections will be use: 
1. Deck metadata. Has deck been updated? Other details...
2. Deck Cards: For each deck, what cards does it run? Is it legal?
3. Commander Cards: For each commander, what cards does it run? In what quantities?
"""

# TODO: Fix importing commanders with '.' in the name... publicId = SLmLYywh7k2IND_xkmcQ5A
import time

from pymongo import MongoClient
import datetime
from dateutil import parser
from utils import normalize_text
from scryfall import get_card_data

client = MongoClient("mongodb://pdhrec:70GCvU3l6BvGBSQKcQcfnuWgG2H4xABMigiJ3CAnYwhVCeWyQrcoRMXHHK3bpgcCn1xVSAa94xZYOfm3IPiUfw==@pdhrec.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&replicaSet=globaldb&maxIdleTimeMS=120000&appName=@pdhrec@")
# client = MongoClient()
db = client['azure_pdhrec']


def save_metadata(data):
    """
    Inserts deck metadata into the metadata collection, updating if exists already, otherwise inserting.
    :param data: deck metadata, a dict of publicId, id, lastUpdatedAtUtc, name, hasPrimer, needsUpdate.
    :return: None
    """
    # print(data)
    col = db['metadata']
    data["_id"] = data['publicId']
    col.update_one({"_id": data["_id"]}, {"$set": data}, upsert=True)


def load_metadata(publicId):
    return db['metadata'].find_one({"_id": publicId})


def save_cards(data):
    try:
        col = db['decks']
        info = {'_id': data['publicId'], 'cards': {}, 'commanders': {},
                'colors': {'W': False, 'U': False, 'B': False,
                           'R': False, 'G': False}}
        for card in data['mainboard']:
            if data['mainboard'][card]['card']['legalities']['paupercommander'] != "legal":
                return False
            info['cards'][card] = data['mainboard'][card]["quantity"]

        # print(info)

        for card in data['commanders']:
            for color in data['commanders'][card]['card']['colors']:
                info['colors'][color] = True
            info['commanders'][card] = data['commanders'][card]['quantity']
            if data['commanders'][card]['card']['legalities']['paupercommander'] == "restricted":
                pass
            elif data['commanders'][card]['card']['legalities']['paupercommander'] == "legal":
                if data['commanders'][card]['card']['rarity'] == "uncommon" and \
                        data['commanders'][card]['card']['type'] == "2":
                    pass
                else:
                    return False
            else:
                return False
            save_card_data(card)
            if card == "Mr. Orfeo, the Boulder":
                card2 = "Mr Orfeo, the Boulder"
                info['commanders'][card2] = info['commanders'][card]
                info['commanders'].pop(card)
        info['commanderstring'] = "-".join(normalize_text([x for x in info['commanders']]))
        mainboard = 0
        for card in info['cards']:
            mainboard += info['cards'][card]
        for card in info['commanders']:
            mainboard += info['commanders'][card]
        if mainboard != 100:
            return False
        if not 0 < len(info['commanders']) <= 2:
            return False
        print("Inserting cards..")
        print(info)
        # Does it already exist in the database?
        result = col.find_one({"_id": info['_id']})
        if result is None:
            add_to_scores(info)

            col.insert_one(info)
        else:
            subtract_from_scores(result)
            add_to_scores(info)
            col.update_one({'_id': info['_id']}, {"$set": info}, upsert=True)
    except Exception as e:
        print(e)
        return False
    return True


def get_synergy_scores(commanders):
    # score is % of decks the card is in for the commander, - % of cards in the deck for all decks

    one = get_commander_aggregate_bad(commanders)

    two = get_commander_aggregate_bad([])

    scores = {}
    for card in one:
        a = one[card] / get_decks_with_commanders(commanders)
        b = two[card] / get_decks_with_commanders([])
        scores[card] = a - b
    return scores


def get_new_synergy_scores(commanderstring):
    tik = time.time()
    # Figure this out later...
    # commanders = "-".join(sorted(normalize_text(commanders)))
    col = db['scores']
    print(time.time() - tik)
    commander_data = col.find_one({"commanderstring": commanderstring})
    print(time.time() - tik)
    if commander_data is None:
        return {}
    scores = {}
    print(time.time() - tik)
    all_decks = new_count_all_decks()
    for card in commander_data['cards']:
        a = commander_data["cards"][card] / commander_data['count']
        b = db['alldeckscores'].find_one({"name": card})['count'] / all_decks
        scores[card] = a - b
    print(time.time() - tik)
    return scores


def load_cards(publicId):
    pass


def get_ids_need_update():
    col = db['metadata']
    return [x['_id'] for x in col.find({"needsUpdate": True})]


def get_newest_metadata():
    col = db['metadata']
    col.find_one()
    return list(reversed(sorted([x['lastUpdatedAtUtc'] for x in db['metadata'].find({})])))[0]
    # return [x for x in db['metadata'].find().sort(["lastUpdatedAtUtc"], [-1]).limit(1)][0]


def get_all_metadata():
    return db['metadata'].find({})


def get_commander_aggregate(commanders):
    col = db['decks']
    if len(commanders) == 2:
        match = {"$and": [{f"commanders.{commanders[0]}": {"$exists": 1}}, {f"commanders.{commanders[1]}": {
            "$exists": 1}}]}
    elif len(commanders) == 1:
        match = {f"commanders.{commanders[0]}": {"$exists": 1}}
    else:
        match = {}
    # print({"$match": match})
    result = col.aggregate(pipeline=[
        {"$match": match},
        # {"$project": {"_id": 0, "cards": 1}},

    ])
    return result


def get_commander_aggregate_bad(commanders):
    decks = get_commander_aggregate(commanders)
    sums = {}
    for deck in decks:
        for card in deck['cards']:
            if card not in sums:
                sums[card] = 0
            # sums[card] += deck['cards'][card]
            sums[card] += 1  # Fixed to one win per card.  Reduces shifting from rat colony type cards
    return sums


def get_decks_with_commanders(commanders):
    return len([x for x in get_commander_aggregate(commanders)])


def new_get_all_commander_counts():
    col = db['scores']
    results = col.aggregate(pipeline=[
        # {
        #     "$lookup":
        #     {
        #         "from": "cards",
        #         "localField": "commanderstring",
        #         "foreignField": "normalized",
        #         "as": "data"
        #     }
        # },
        {
            "$lookup":
            {
                "from": "cards",
                "localField": "commanders.0",
                "foreignField": "name",
                "as": "partner1"
            }
         },
        {
            "$lookup":
                {
                    "from": "cards",
                    "localField": "commanders.1",
                    "foreignField": "name",
                    "as": "partner2"
                }
        },
        {"$project": {"_id": 0, "commanderstring": 1, "commanders": 1, "count": 1, "partner1": 1,
                      "partner2": 1}},
    ])
    return [x for x in results]


def get_all_staples():

    col = db['scores']
    data = col.find_one({"commanderstring": ""})
    data.pop("_id")
    return data

def new_count_all_decks():
    col = db['decks']
    return col.count()


def get_all_commanders_and_counts():
    in_data = get_commander_aggregate([])
    out_data = {}
    for deck in in_data:
        commanders = sorted([key for key in deck['commanders']])
        commanders = normalize_text(commanders)
        if "-".join(commanders) not in out_data:
            out_data["-".join(commanders)] = 0
        out_data["-".join(commanders)] += 1
    return out_data


def save_card_data(card_name):
    col = db['cards']

    data = get_card_data(card_name)
    exists = col.find_one({"_id": data['id']})
    if exists is not None and len([x for x in exists]) != 0:
        return
    to_write = {}

    to_write["_id"] = data['id']
    to_write["name"] = data['name']
    to_write["normalized"] = normalize_text([data['name']])[0]
    to_write["image"] = data['image_uris']['large'] if 'large' in data['image_uris'] else \
        data['image_uris'][list(data['image_uris'].keys())[0]]
    to_write["colors"] = data['color_identity']

    if to_write['name'] == "Mr. Orfeo, the Boulder":
        to_write['name'] = "Mr Orfeo, the Boulder"

    col.insert_one(to_write)


def add_to_scores(deck_data):
    time.sleep(1)
    commanders = normalize_text([x for x in deck_data['commanders']])
    commanders.sort()
    print(commanders)
    col = db['scores']
    result = col.find_one({"commanderstring": "-".join(commanders)})
    if result is None:
        col.insert_one({"commanderstring": "-".join(commanders), "cards": {}, "count": 0})
        result = col.find_one({"commanderstring": "-".join(commanders)})
    for card in deck_data['cards']:
        if card not in result['cards']:
            col.update_one({"name": card}, {"$set": {"cards." + card: 0}})
        col.update_one({"name": card}, {"$inc": {"cards." + card: 1}})
        # result['cards'][card] += 1
    result['count'] += 1
    result['commanders'] = sorted([x for x in deck_data['commanders']])
    col.update_one({'commanderstring': '-'.join(commanders)}, {"$set": result}, upsert=True)
    col = db['alldeckscores']
    for card in deck_data['cards']:
        result = col.find_one({"name": card})
        if result is None:
            col.insert_one({"name": card, "count": 1})
        else:
            col.update_one({'name': card}, {"$inc": {"count": 1}})


def subtract_from_scores(deck_data):
    commanders = normalize_text([x for x in deck_data['commanders']])
    commanders.sort()
    print(commanders)
    col = db['scores']
    result = col.find_one({"commanderstring": "-".join(commanders)})
    if result is None:
        print("Subtracting when none to subtract..")
        return False
    for card in deck_data['cards']:
        if card not in result['cards']:
            print("Error, card not existing for subtraction. ")
            return False
        result['cards'][card] -= 1
    result['count'] -= 1
    col.update_one({'commanderstring': '-'.join(commanders)}, {"$set": result}, upsert=True)
    col = db['alldeckscores']
    for card in deck_data['cards']:
        if col.find_one({"name": card}) is None:
            print("Error, card not existing for subtraction. ")
            return False
        else:
            col.update_one({"name": card}, {"$inc": {"count": -1}})


if __name__ == "__main__":
    # in_the_deck = get_commander_aggregate_bad(["Crypt Rats"])
    # in_all_decks = get_commander_aggregate_bad([])
    # scores = {}
    # for card in in_the_deck:
    #     scores[card] = in_the_deck[card] / in_all_decks[card]
    # results = get_synergy_scores(["Vizkopa Guildmage"])
    # results = dict(sorted(results.items(), key=lambda item: -item[1]))
    # for x in results:
    #     print(f"{x}:{results[x]}")
    # results = get_commander_aggregate(["Ley Weaver", "Lore Weaver"])
    # results = get_all_commanders_and_counts()
    # results = dict(sorted(results.items(), key=lambda item: -item[1]))
    # from moxfield import get_deck_data
    # card_data = get_deck_data("wc2xdCuzE027BF9NmsXpZg")
    # insert_deck_cards(card_data)

    print(get_all_staples())
