"""
Accessing scryfall for card images.
"""
import time
import requests
from dateutil import parser
from urllib.parse import quote
from backend.utils import normalize_cardname
from backend.card import Card
from backend.legality import card_legal_as_commander, card_legal_in_main

cards = {}


def get_card_object(name):
    """
    Query and return card data from Scryfall.
    """
    card = Card()

    if name in cards:
        print("Using cached")
        scryfall_card_data = cards[name]
    else:
        time.sleep(50 / 1000)  # Avoid overloading Scryfall API
        print("Searching")
        card_request = requests.get(
            f"https://api.scryfall.com/cards/search?q=\"{quote(name)}\"&order=released&dir=asc&unique=prints")
        if card_request.status_code != requests.codes.ok:
            return False
        scryfall_card_data = card_request.json()['data']

    # Filter query to only cards exactly matching name
    scryfall_card_data = [card for card in scryfall_card_data if
                          card["name"] == name]
    if scryfall_card_data == []:  # Create invalid card
        card.name = name
        card.legal_as_commander = False
        card.legal_in_mainboard = False
        card.image_urls = []
        card.time_first_printed = -1
        card.color_identities = []
        return card

    # Create card object
    card.name = name
    card.legal_as_commander = card_legal_as_commander(scryfall_card_data)
    card.legal_in_mainboard = card_legal_in_main(scryfall_card_data)
    try:
        # Find standard card art
        possible_cards = [card for card in scryfall_card_data if
                          (not card['digital'] and card['highres_image'] and
                           "etched" not in card['finishes'] and
                           ("frame_effects" not in card or
                            "showcase" not in card["frame_effects"]) and
                           card["set"] != "sld")]
        card.image_urls = choose_image(possible_cards)
    except Exception as e:
        print(e)
        # Try second most recent image
        if len(scryfall_card_data) > 1:
            try:
                card.image_urls = choose_image(possible_cards, -2)
            except Exception as e:
                print(e)
                possible_cards = [card for card in scryfall_card_data if (not card['digital'])]
                card.image_urls = choose_image(possible_cards)

    card.time_first_printed = parser.parse(
        scryfall_card_data[0]['released_at']).timestamp()
    card.color_identities = "".join(scryfall_card_data[0]['color_identity'])

    return card


def query_scryfall(card_name):
    card_name = normalize_cardname(card_name)
    url = f"https://api.scryfall.com/cards/named?exact={card_name}"
    r = requests.get(url)
    return r.json()


def choose_image(possible_cards, image_index=-1):
    """
    Accessing the card at the given index (default -1) in the list of possible 
    cards, return the best image URL.
    """
    images = []
    if ("image_uris" not in possible_cards[image_index] and
            "card_faces" in possible_cards[image_index]):
        for face in possible_cards[image_index]["card_faces"]:
            images.append(face['image_uris']['large'])
    else:
        images.append(possible_cards[image_index]['image_uris']['large'])
    return images


def get_card_names_for_cards_needing_updates(most_recent_updated_card_time):
    # Scratch work to get the latest sets that are not spoilers:
    sets_url = """https://api.scryfall.com/sets"""
    r = requests.get(sets_url)
    set_data = r.json()['data']
    set_data = sorted(set_data,
                      key=lambda x: -parser.parse(x['released_at']).timestamp())

    # Select out the ones that are in the future:
    start = 0
    while start < len(set_data) - 1:
        if parser.parse(
                set_data[start]['released_at']).timestamp() < time.time():
            break
        start += 1

    # Find the end based on the database
    end = start
    while end < len(set_data) - 1:
        if parser.parse(set_data[end]['released_at']).timestamp() < \
                most_recent_updated_card_time:
            break
        end += 1

    print(set_data[start:end])

    # Filter out art cards:
    set_data = [x for x in set_data[start:end] if x['set_type']
                not in ("memorabilia", "token")]

    if len(set_data) == 0:
        return []

    query = "(game:paper or game:mtgo)(" + " or ".join(["e:" + x['code'] for
                                                        x in
                                                        set_data]) + ")"

    r = requests.get(f"https://api.scryfall.com/cards/search?q={query}")
    decoded = r.json()
    data = []
    for item in decoded['data']:
        data.append(item)
    while decoded['has_more']:
        print(len(data))
        r = requests.get(decoded['next_page'])
        decoded = r.json()
        for item in decoded['data']:
            data.append(item)

    return [x['name'] for x in data]


if __name__ == "__main__":
    print(len(get_card_names_for_cards_needing_updates(1687492800)))
