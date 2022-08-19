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
from utils import normalize_text
from scryfall import get_card_data

client = MongoClient(
    "mongodb://pdhrec:70GCvU3l6BvGBSQKcQcfnuWgG2H4xABMigiJ3CAnYwhVCeWyQrcoRMXHHK3bpgcCn1xVSAa94xZYOfm3IPiUfw==@pdhrec.mongo.cosmos.azure.com:10255/?ssl=true&retrywrites=false&replicaSet=globaldb&maxIdleTimeMS=120000&appName=@pdhrec@")
# client = MongoClient("mongodb+srv://origamiimaster:<password>@pdhrec.pfi73ng.mongodb.net/?retryWrites=true&w=majority")
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
    data["_id"] = data['publicId'] + "metadata"
    data["type"] = "metadata"
    data['commandername'] = ""
    col.update_one({"_id": data["_id"], "type": "metadata"}, {"$set": data}, upsert=True)


def load_metadata(publicId):
    return db['metadata'].find_one({"_id": publicId + "metadata", "type": "metadata"})


def save_cards(data):
    # try:
    col = db['metadata']
    info = {'_id': data['publicId'] + "deck", 'cards': {}, 'commanders': {},
            'colors': {'W': False, 'U': False, 'B': False,
                       'R': False, 'G': False}, "type": "deck"}
    for card in data['mainboard']:
        if "paupercommander" not in data['mainboard'][card]['card']['legalities'] or data['mainboard'][card]['card']['legalities']['paupercommander'] != "legal":
            return False
        info['cards'][card] = data['mainboard'][card]["quantity"]

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
        # url = save_card_data(card)
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
    info['commandername'] = ""
    # Does it already exist in the database?
    result = col.find_one({"_id": info['_id'], "type": "deck"})
    if result is None:
        add_to_scores(info)

        col.insert_one(info)
    else:
        subtract_from_scores(result)
        add_to_scores(info)
        info['type'] = "deck"
        col.update_one({'_id': info['_id'], "type": "deck"}, {"$set": info}, upsert=True)

    return True


def get_new_synergy_scores(commanderstring):
    # tik = time.time()
    # Figure this out later...
    # commanders = "-".join(sorted(normalize_text(commanders)))
    col = db['scores']
    # print(time.time() - tik)
    commander_data = col.find_one({"commanderstring": commanderstring})
    # print(time.time() - tik)
    if commander_data is None:
        return {}
    scores = {}
    # print(time.time() - tik)
    all_decks = db['scores'].find_one({"commanderstring": ""})
    for card in commander_data['cards']:
        a = commander_data["cards"][card] / commander_data['count']
        b = all_decks['cards'][card] / all_decks['count']
        scores[card] = a - b
    # print(time.time() - tik)
    return scores


def get_ids_need_update():
    col = db['metadata']
    return [x['publicId'] for x in col.find({"needsUpdate": True})]


def get_newest_metadata():
    col = db['metadata']
    col.find_one()
    return list(reversed(sorted([x['lastUpdatedAtUtc'] for x in db['metadata'].find({"type": "metadata"})])))[0]


def get_all_metadata():
    return db['metadata'].find({})


def new_get_all_commander_counts():
    col = db['scores']
    results = col.aggregate(pipeline=[
        # {
        # "$lookup":
        # {
        # "from": "metadata",
        # "localField": "commanders.0",
        # "foreignField": "commandername",
        # "as": "partner1"
        # }
        # },
        # {
        # "$lookup":
        # {
        # "from": "metadata",
        # "localField": "commanders.1",
        # "foreignField": "commandername",
        # "as": "partner2"
        # }
        # },
        {"$project": {"_id": 0, "commanderstring": 1, "commanders": 1, "count": 1, "urls": 1}},
    ])
    return [x for x in [x for x in results] if x['commanderstring'] != '']


def new_count_all_decks():
    pass
    # col = db['decks']
    # return col.count()


def save_card_data(card_name):
    try:
        col = db['metadata']

        data = get_card_data(card_name)
        exists = col.find_one({"_id": data['id'] + "card", "type": "card"})
        if exists is not None and len([x for x in exists]) != 0:
            return
        to_write = {}

        to_write["_id"] = data['id'] + "card"
        to_write["type"] = "card"
        to_write["name"] = data['name']
        to_write["commandername"] = data['name']
        to_write["normalized"] = normalize_text([data['name']])[0]
        to_write["image"] = data['image_uris']['large'] if 'large' in data['image_uris'] else \
            data['image_uris'][list(data['image_uris'].keys())[0]]
        to_write["colors"] = data['color_identity']

        if to_write['name'] == "Mr. Orfeo, the Boulder":
            to_write['name'] = "Mr Orfeo, the Boulder"
            to_write['commandername'] = "Mr Orfeo, the Boulder"

        col.insert_one(to_write)
    except Exception as e:
        print(e)


def get_card_url(card_name):
    try:
        data = get_card_data(card_name)
        return data["image_uris"]["large"] if "large" in data["image_uris"] else data["image_uris"][
            list(data['image_uris'].keys())[0]]
    except Exception as e:
        print(e)
        return "https://c1.scryfall.com/file/scryfall-cards/large/front/8/0/8059c52b-5d25-4052-b48a-e9e219a7a546.jpg?1594736914"


def add_to_scores(deck_data, commander=True):
    if commander:
        commanders = normalize_text([x for x in deck_data['commanders']])
        commanders.sort()
    else:
        commanders = [""]
    print(commanders)
    col = db['scores']
    result = col.find_one({"commanderstring": "-".join(commanders)})
    if result is None:
        to_insert = {"commanderstring": "-".join(commanders), "cards": {}, "count": 0}
        if commander is True:
            to_insert["urls"] = []
            for commander in deck_data["commanders"]:
                to_insert["urls"].append(get_card_url(commander))
            # to_insert["partner1"] = get_card_url()
        col.insert_one(to_insert)
        result = col.find_one({"commanderstring": "-".join(commanders)})
    for card in deck_data['cards']:
        if card not in result['cards']:
            result['cards'][card] = 0
            # col.update_one({"name": card}, {"$set": {"cards." + card: 0}})
        # col.update_one({"name": card}, {"$inc": {"cards." + card: 1}})
        result['cards'][card] += 1
    result['count'] += 1
    result['commanders'] = sorted([x for x in deck_data['commanders']])
    col.update_one({'commanderstring': '-'.join(commanders)}, {"$set": result}, upsert=True)
    if commander:
        add_to_scores(deck_data, False)


def subtract_from_scores(deck_data, commander=True):
    if commander:
        commanders = normalize_text([x for x in deck_data['commanders']])
        commanders.sort()
    else:
        commanders = [""]
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

    if commander:
        subtract_from_scores(deck_data, False)
    # if commanders[0] == "" and len(commanders) == 1:
    #     pass
    # else:
    #     deck_data['commanders'] = [""]
    #     subtract_from_scores(deck_data)

    # col = db['alldeckscores']
    # for card in deck_data['cards']:
    #     if col.find_one({"name": card}) is None:
    #         print("Error, card not existing for subtraction. ")
    #         return False
    #     else:
    #         col.update_one({"name": card}, {"$inc": {"count": -1}})


def check_commander_exists(commander_name) -> bool:
    col = db['scores']
    if col.find_one({"commanderstring": commander_name}) is None:
        return False
    return True


def get_commander_names():
    col = db['scores']
    results = col.aggregate(pipeline=[
        {"$project": {"_id": 0, "commanderstring": 1, "commanders": 1}},
    ])
    return results

def get_commander_data(commander_name):
    col = db['scores']
    results = col.aggregate(pipeline=[
        {"$match": {"commanderstring": commander_name}},
        {"$project": {"_id": 0, "commanderstring": 1, "commanders": 1, "urls": 1, "count": 1}},
    ])
    # print(results)
    return results.next()

def add_website_visit():
    col = db["metadata"]
    if col.find_one({"type": "visits"}) is None:
        col.insert_one({"type":"visits", "_id":"visits", "count": 0})
    data = col.find_one({"type":"visits"})
    data["count"] += 1
    col.update_one({"type":"visits"}, {"$set": data})

def get_website_visit():
    col = db["metadata"]
    if col.find_one({"type":"visits"}) is None:
        return 0
    return col.find_one({"type":"visits"})["count"]

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
    # save_cards(card_data)
    col = db['metadata']
    data = new_get_all_commander_counts()
    print(data)
    print(get_card_url("Colossal Dreadmaw"))
