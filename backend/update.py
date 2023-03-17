"""
Periodically update the data on decks.
"""
import json
import os
import time
import requests

from dateutil import parser

from backend.database import Database
from backend.moxfield import convert_to_deck, get_deck_data, get_new_decks
from backend.scryfall import get_card_data_as_card_object


def check_legal(deck, cards_so_far, database):
    # Check if len(commanders) == 1 or len(commanders) == 2:
    if not (0 < len(deck['commanders']) <= 2):
        print(f"Wrong number of commanders: {len(deck['commanders'])}")
        return False
    commander_color_identities = set()
    for commander in deck['commanders']:
        if commander not in cards_so_far:
            cards_so_far[commander] = database.get_card(commander)
        if cards_so_far[commander] is None:
            print(f"Missing commander from database {commander}")
            database.insert_card({"name": commander, "needsUpdate": True})
            return False
        if not cards_so_far[commander]['legal_as_commander']:
            print(f"Illegal Commander {commander}")
            return False
        commander_color_identities.update(set(cards_so_far[commander]['color_identities']))

    for card in deck['cards']:
        if card not in cards_so_far:
            cards_so_far[card] = database.get_card(card)
        if cards_so_far[card] is None:
            print(f"Missing card from database {card}")
            return False
        if not cards_so_far[card]['legal_in_mainboard']:
            print(f"Illegal card: {card}")
            return False
        if not all(x in commander_color_identities for x in cards_so_far[card]['color_identities']):
            print(f"Illegal color identities: {card}, {deck['commanders']}")
            return False
    return True


def get_latest_bulk_file(database, directory="../scryfall_data"):
    """
    Gets the latest "oracle-data" cards and then saves them to a file labeled "oracle-data-X.json".
    :return:
    """
    r = requests.get("https://api.scryfall.com/bulk-data")
    data = r.json()
    oc_version = [x for x in data['data'] if x['type'] == "oracle_cards"][0]
    print("Checking bulk file version")
    if not os.path.isfile(f"{directory}/{oc_version['download_uri'].split('/')[-1]}"):
        print("New bulk file found")
        r = requests.get(oc_version["download_uri"])
        with open(f"{directory}/{oc_version['download_uri'].split('/')[-1]}", "wb") as f:
            f.write(r.content)
        # Now delete the other versions
        data_files = os.listdir(f"{directory}")
        for file in data_files:
            if file == oc_version['download_uri'].split('/')[-1]:
                pass
            else:
                print(f"Deleting {file}")
                os.remove(f"{directory}/{file}")

        # Since we've got a new file, some cards can have changed rarities.  Switch over the "needs legality check"
        # flag.
        # database.cards.update_many({}, {"$set": {"needsUpdate": True}})
        # database.decks.update_many({}, {"$set": {"needsLegalityCheck": True}})
        return f"{directory}/{oc_version['download_uri'].split('/')[-1]}"
    else:
        print("No new bulk file found")
        return f"{directory}/{oc_version['download_uri'].split('/')[-1]}"


def perform_update(database):
    print("Auto updating decks to database")
    # Step 1: Update decks
    # Find the most recently updated deck in the database, then iterate backwards from there
    latest = database.decks.find_one(sort=[("update_date", -1)])
    latest_time = latest['update_date']
    new_decks = get_new_decks()
    newest_deck = new_decks[0]
    newest_time = parser.parse(newest_deck['lastUpdatedAtUtc']).timestamp()
    if latest_time < newest_time:
        print("Updating")
        time_to_reach = latest_time
        last_deck_time = newest_time

        page = 1
        while time_to_reach < last_deck_time:
            for deck in new_decks:
                print(f"Saving deck {deck['name']}")
                deck_obj = convert_to_deck(get_deck_data(deck['publicId'])).to_dict()
                deck_obj['needsLegalityCheck'] = True

                database.insert_deck(deck_obj)
                last_deck_time = deck_obj['update_date']
                if time_to_reach >= last_deck_time:
                    break
            page += 1
            time.sleep(1)
            new_decks = get_new_decks(page)
    else:
        pass
    # Step 2: Update all cards.
    # Then have the database update any cards in need of an update:
    # cursor = database.cards.find({"needsUpdate": True})
    # entries_in_mem = [x for x in cursor]
    # entries_in_mem = database.cards.find({})
    entries_in_mem = database.cards.find({"needsUpdate": True})

    for entry in entries_in_mem:
        print(f"Updating card {entry['name']}")
        tik = time.time()
        card = get_card_data_as_card_object(entry['name'])
        if card is False:
            card = entry
            card['needsUpdate'] = False
            # card['needsLegalityCheck'] = False
            card['legal_in_mainboard'] = False
            card['legal_as_commander'] = False
            card['error'] = True
            database.insert_card(card)
            print(time.time() - tik)

        else:
            card = card.to_dict()
            database.insert_card(card)
            print(time.time() - tik)

    # Step 3:
    # Check each deck for illegal cards
    #
    # database.decks.update_many({}, {"$set": {"needsLegalityCheck": True}})
    cards_so_far = {}
    for deck in database.decks.find({"needsLegalityCheck": True}):
        print(deck)
        legal = check_legal(deck, cards_so_far, database)
        deck['needsLegalityCheck'] = False
        deck['isLegal'] = legal
        database.insert_deck(deck)
        if not legal:
            print(f"Illegal deck: https://moxfield.com/decks/{deck['_id']}")

def load_all_decks_backwards(database):
    """
    Manually load decks backward (up to a maximum timestamp distance)
    :param database:
    :return:

    import json
    from backend.update import load_all_decks_backwards
    from backend.database import Database
    with open("server-token.json") as f:
        connection_string = json.load(f)['connection']
    database = Database(connection_string)
    load_all_decks_backwards(database)

    """
    latest = database.decks.find_one(sort=[("update_date", -1)])
    latest_time = latest['update_date']
    new_decks = get_new_decks()
    page = 1
    oldest_deck = new_decks[-1]
    oldest_time = parser.parse(oldest_deck['lastUpdatedAtUtc']).timestamp()
    print(f"Looking for time {latest_time} for deck {latest['_id']}")
    while latest_time < oldest_time:
        page += 1
        new_decks = get_new_decks(page)
        oldest_deck = new_decks[-1]
        oldest_time = parser.parse(oldest_deck['lastUpdatedAtUtc']).timestamp()

    print(oldest_time)
    print(oldest_deck)

    while len(new_decks) != 0:
        print(f"Page = {page}")
        for deck in new_decks:
            print(f"Saving deck {deck['name']}, {deck['publicUrl']}")
            deck_obj = convert_to_deck(get_deck_data(deck['publicId'])).to_dict()
            deck_obj['needsLegalityCheck'] = True

            database.insert_deck(deck_obj)
            last_deck_time = deck_obj['update_date']
            # if time_to_reach >= last_deck_time:
            #     break
        page += 1
        time.sleep(1)
        new_decks = get_new_decks(page)



if __name__ == "__main__":
    with open("../server-token.json") as f:
        connection_string = json.load(f)['connection']
    database = Database(connection_string)
    # Begin an auto update?
    # get_latest_bulk_file(database)
    perform_update(database)
