"""
Access moxfield and query decks for inclusion in the database.

"""

import requests
# from database import Database, get_new_decks

def get_deck_data(public_id):
    url = f"https://api.moxfield.com/v2/decks/all/{public_id}"
    r = requests.get(url)
    if r.status_code != 200:
        return False
    return r.json()


def get_deck_information(deck_id):
    pass


if __name__ == "__main__":


    deck = get_deck_data("LXiuz3D1DkO8m4mxBKVNGg")

    # new_decks = get_new_decks()
    # for deck in new_decks:
    #     db.update_deck(deck)
    #     time.sleep(1)
