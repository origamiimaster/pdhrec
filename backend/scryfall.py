"""
Accessing scryfall for card images...
"""
import requests
from dateutil import parser
from urllib.parse import quote

from backend.card import Card
from backend.legality import check_card_allowed_as_commander, check_card_allowed_in_main

def get_card_data_as_card_object(name, use_json=True):
    """
    Gets the Scryfall card information, and returns the necessary values

    :param name:
    :param use_json:
    :return:
    """
    card = Card()
    with requests.get(f"https://api.scryfall.com/cards/search?q=\""
                      f"{quote(name)}\"&order=released&dir=asc&unique=prints") as r:
        scryfall_card_data = r.json()['data']
    scryfall_card_data = [x for x in scryfall_card_data if x["name"] == name]
    card.name = name
    card.legal_as_commander = check_card_allowed_as_commander(scryfall_card_data)
    card.legal_in_mainboard = check_card_allowed_in_main(scryfall_card_data)
    image_index = -2 if len(scryfall_card_data) > 1 else -1
    if "image_uris" not in scryfall_card_data[image_index] and "card_faces" in scryfall_card_data[image_index]:
        for face in scryfall_card_data[image_index]["card_faces"]:
            card.image_urls.append(face['image_uris']['large'])
    else:
        try:
            card.image_urls.append(scryfall_card_data[image_index]['image_uris']['large'])
        except KeyError:
            pass
    card.time_first_printed = parser.parse(scryfall_card_data[0]['released_at']).timestamp()
    card.color_identities = "".join(scryfall_card_data[0]['color_identity'])
    return card

def get_card_data(card_name):
    card_name = ''.join(char for char in ["+" if c == " " else c for c in card_name.lower()] if char.isalnum() or char == "+")
    url = f"https://api.scryfall.com/cards/named?exact={card_name}"
    r = requests.get(url)
    return r.json()
