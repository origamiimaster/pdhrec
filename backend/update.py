"""
Periodically update the data on decks.
"""
import json
import time

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


if __name__ == "__main__":
    with open("../server-token.json") as f:
        connection_string = json.load(f)['connection']
    database = Database(connection_string)
    # Begin an auto update?
    print("Auto updating decks to database")

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

    # Temporary measure: Iterate through the latest 10 moxfield decks and attempt to add them.
    # deck_infos = get_new_decks()[:10]
    #
    # for deck_info in deck_infos:
    #     ti = time.time()
    #     deck = convert_to_deck(get_deck_data(deck_info['publicId']))
    #     database.insert_deck(deck.to_dict())
    #     print(time.time() - ti)
    #
    # Then have the database update any cards in need of an update:
    cursor = database.cards.find({"needsUpdate": True})
    entries_in_mem = [x for x in cursor]

    for entry in entries_in_mem:
        tik = time.time()
        card = get_card_data_as_card_object(entry['name']).to_dict()
        card['needsUpdate'] = False
        card['needsLegalityCheck'] = True
        card['isLegal'] = False
        database.insert_card(card)
        print(time.time() - tik)

    # Chunk it by 100 entries?
    # for sublist in [entries_in_mem[n:n+100] for n in range(0, len(entries_in_mem), 100)]:
    #     to_add = []
    #     ti = time.time()
    #     time.sleep(50 / 1000)
    #     for value in sublist:
    #         print(value['name'])
    #         card_obj = get_card_data_as_card_object(value['name']).to_dict()
    #         card_obj['needsUpdate'] = False
    #     database.insert_card(card_obj)
    #     print(time.time() - ti)

    # Check each deck for illegal cards
    cards_so_far = {}
    for deck in database.decks.find({"needsLegalityCheck": True}):
        print(deck)
        legal = check_legal(deck, cards_so_far, database)
        deck['needsLegalityCheck'] = False
        deck['isLegal'] = legal
        database.insert_deck(deck)
        if not legal:
            print(f"Illegal deck: https://moxfield.com/decks/{deck['_id']}")
