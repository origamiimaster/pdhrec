"""
Accessing scryfall for card images.
"""
import time
import requests
from dateutil import parser
from urllib.parse import quote
import json

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
        time.sleep(50/1000) # Avoid overloading Scryfall API
        print("Searching")
        card_request = requests.get(f"https://api.scryfall.com/cards/search?q=\"{quote(name)}\"&order=released&dir=asc&unique=prints")
        if card_request.status_code != requests.codes.ok:
            return False
        scryfall_card_data = card_request.json()['data']

    # Filter query to only cards exactly matching name
    scryfall_card_data = [card for card in scryfall_card_data if card["name"] == name]
    if scryfall_card_data == []: # Create invalid card
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
            except KeyError:
                pass

    card.time_first_printed = parser.parse(scryfall_card_data[0]['released_at']).timestamp()
    card.color_identities = "".join(scryfall_card_data[0]['color_identity'])

    return card



def query_scryfall(card_name):
    card_name = normalize_cardname(card_name)
    url = f"https://api.scryfall.com/cards/named?exact={card_name}"
    r = requests.get(url)
    return r.json()


def choose_image(possible_cards, image_index = -1):
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


if __name__ == "__main__":
    pass
    # with open("../default-cards.json", "r") as f:
    #     scryfall_download = json.load(f)
    #     cards = {}
    #     for card in scryfall_download:
    #         if card['name'] not in cards:
    #             cards[card['name']] = []
    #         cards[card['name']].append(card)
