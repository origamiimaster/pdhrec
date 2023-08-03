"""
Access moxfield and query decks for inclusion in the database.
"""

from typing import Optional
import requests
from dateutil import parser
from backend.deck import Deck


def get_deck_data(deck_id: str) -> Optional[dict]:
    """
    Query moxfield for a deck's information given the deck ID.

    :param deck_id: Deck ID on Moxfield
    :return: Return the deck information as a dictionary if found.
    Otherwise, return None.
    """
    url = f"https://api.moxfield.com/v2/decks/all/{deck_id}"
    deck_request = requests.get(url)
    if deck_request.status_code != 200:
        return None
    return deck_request.json()


def get_new_decks(page: int = 1) -> list[dict]:
    """
    Query the given page in the moxfield list of new decks (in reverse
    chronological order). If page not given, return the first page.

    :param page: Page of the list of new decks to return
    :return: metadata on most recent decks, as list of dictionaries
    """
    url = f"""https://api.moxfield.com/v2/decks/search?pageNumber={page}&pageSize=64&sortType=updated&sortDirection=Descending&fmt=pauperEdh&board=mainboard"""
    decks_request = requests.get(url)
    return decks_request.json()['data']


def convert_to_deck(moxfield_deck_data: dict) -> Deck:
    """
    Convert the Moxfield deck dictionary format (eg from get_deck_data)
    to a Deck object.

    :param moxfield_deck_data: Moxfield deck data, as a dictionary
    :return: Deck object with the same information
    """
    deck_obj = Deck()
    for commander_name in moxfield_deck_data['commanders']:
        deck_obj.commanders.append(commander_name)
    for card_name in moxfield_deck_data['mainboard']:
        for _ in range(moxfield_deck_data['mainboard'][card_name]['quantity']):
            deck_obj.main_board.append(card_name)
    deck_obj.id = moxfield_deck_data['publicId']
    deck_obj.last_updated = parser.parse(moxfield_deck_data['lastUpdatedAtUtc']).timestamp()
    return deck_obj


if __name__ == "__main__":
    deck = get_deck_data("LXiuz3D1DkO8m4mxBKVNGg")
    parsed = convert_to_deck(deck)
    # new_decks = get_new_decks()
    # for deck in new_decks:
    #     db.update_deck(deck)
    #     time.sleep(1)
