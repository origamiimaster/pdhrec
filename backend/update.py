"""
Periodically update the data on decks.
"""
import json
import time

from backend.database import Database
from backend.moxfield import convert_to_deck, get_deck_data, get_new_decks
from backend.scryfall import get_card_data_as_card_object

if __name__ == "__main__":
    with open("../server-token.json") as f:
        connection_string = json.load(f)['connection']
    database = Database(connection_string)
    # Begin an auto update?
    print("Auto updating decks to database")

    # Temporary measure: Iterate through the latest 10 moxfield decks and attempt to add them.
    deck_infos = get_new_decks()[:]

    for deck_info in deck_infos:
        ti = time.time()
        deck = convert_to_deck(get_deck_data(deck_info['publicId']))
        database.insert_deck(deck.to_dict())
        print(time.time() - ti)

    # Then have the database update any cards in need of an update:
    cursor = database.cards.find({"needsUpdate": True})
    for value in cursor:
        ti = time.time()
        time.sleep(0.01)
        print(value['name'])
        card_obj = get_card_data_as_card_object(value['name']).to_dict()
        card_obj['needsUpdate'] = False
        database.insert_card(card_obj)
        print(time.time() - ti)

