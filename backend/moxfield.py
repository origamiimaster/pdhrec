"""
Access moxfield and query decks for inclusion in the database.
"""

import requests
from dateutil import parser

from backend.deck import Deck


def get_deck_data(public_id):
    """
    Query moxfield for a deck's information, given its ID.
    """
    url = f"https://api.moxfield.com/v2/decks/all/{public_id}"
    deck_request = requests.get(url)
    if deck_request.status_code != 200:
        return False
    return deck_request.json()


def get_new_decks(page = 1):
    """
    Query the moxfield list of new decks (in reverse chrological order). 
    Returns the specified page number, default 1.
    """
    url = f"""https://api.moxfield.com/v2/decks/search?pageNumber={page}&pageSize=64&sortType=updated&sortDirection=Descending&fmt=pauperEdh&board=mainboard"""
    decks_request = requests.get(url)
    values = decks_request.json()['data']
    return values


def convert_to_deck(moxfield_deck_data) -> Deck:
    """
    Converts a moxfield deck format (from get_deck_data) to a Deck object, 
    for database insertion.
    """
    deck = Deck()
    for commander_name in moxfield_deck_data['commanders']:
        deck.commanders.append(commander_name)
    for card_name in moxfield_deck_data['mainboard']:
        for _ in range(moxfield_deck_data['mainboard'][card_name]['quantity']):
            deck.main_board.append(card_name)
    deck.id = moxfield_deck_data['publicId']
    deck.last_updated = parser.parse(moxfield_deck_data['lastUpdatedAtUtc']).timestamp()
    return deck


if __name__ == "__main__":
    deck = get_deck_data("LXiuz3D1DkO8m4mxBKVNGg")
    parsed = convert_to_deck(deck)
    # new_decks = get_new_decks()
    # for deck in new_decks:
    #     db.update_deck(deck)
    #     time.sleep(1)
