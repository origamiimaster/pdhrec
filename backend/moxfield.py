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


def get_new_decks(page=1):
    url = f"""https://api.moxfield.com/v2/decks/search?pageNumber={page}&pageSize=64&sortType=updated&sortDirection=Descending&fmt=pauperEdh&board=mainboard"""
    r = requests.get(url)
    values = r.json()['data']
    return values


def check_deck_legal(deck):
    if deck['mainboardCount'] != 100:
        return False
    if len(deck['commanders']) == 0 or len(deck['commanders']) > 2:
        return False
    for card_name in deck['commanders']:
        if deck['commanders'][card_name]['card']['legalities']['paupercommander'] == "not_legal":
            return False
        if deck['commanders'][card_name]['card']['legalities']['paupercommander'] == "restricted":
            pass  # expected condition
        if deck['commanders'][card_name]['card']['legalities']['paupercommander'] == "legal":
            # Stuff gets complicated here.  If the card was printed at common, but also at uncommon,
            # and is a creature, we allow it.  If the card was printed at common, but not uncommon, we don't allow it.
            # We also will disallow common backgrounds for now, but mainly cause it's easier this way not any other
            # reason.
            if deck['commanders'][card_name]['card']['rarity'] == "uncommon":
                pass
            else:
                return False
    # Now that the commanders are done, we check the cards in the rest of the deck:
    for card_name in deck['mainboard']:
        if deck['mainboard'][card_name]["card"]['legalities']['paupercommander'] == "legal":
            pass
        else:
            return False
    # every card in the deck is checked, everything validated
    return True


if __name__ == "__main__":
    deck = get_deck_data("LXiuz3D1DkO8m4mxBKVNGg")

    # new_decks = get_new_decks()
    # for deck in new_decks:
    #     db.update_deck(deck)
    #     time.sleep(1)