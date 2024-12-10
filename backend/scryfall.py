"""
Accessing Scryfall for card images.
"""
from typing import Optional
import time
import requests
from urllib.parse import quote
from backend.utils import posix_time
import tqdm

def make_scryfall_request(name) -> list:
    tqdm.tqdm.write('Searching')
    scryfall_card_url = f"https://api.scryfall.com/cards/search?q=\"{quote(name)}\"&order=released&dir=asc&unique=prints"
    card_request = requests.get(scryfall_card_url)
    if card_request.status_code != requests.codes.ok:
        print(f'Request failed: Get card from Scryfall: {name}')
        return [{'name': name, 'image_urls': [], 'released': -1,
                 'color_identities': '', 'legal_in_mainboard': False,
                 'legal_as_commander': False, 'needsUpdate': False,
                 'error': True}]
    scryfall_card_data = []
    resp_data = card_request.json()
    scryfall_card_data += resp_data['data']
    while resp_data["has_more"]:
        scryfall_card_url = resp_data["next_page"]
        card_request = requests.get(scryfall_card_url)
        if card_request.status_code != requests.codes.ok:
            print(f'Request failed: Get card from Scryfall: {name}')
            return [{'name': name, 'image_urls': [], 'released': -1,
                     'color_identities': '', 'legal_in_mainboard': False,
                     'legal_as_commander': False, 'needsUpdate': False,
                     'error': True}]
        resp_data = card_request.json()
        scryfall_card_data += resp_data['data']
    return scryfall_card_data


def get_card_from_scryfall(name: str, scryfall_cache: dict) -> dict:
    """
    Query and return card data from Scryfall.

    :param name: Card name to query
    :param scryfall_cache: Cache of cards previously queried on Scryfall
    :return: Dictionary with Scryfall data for database insertion
    """
    # Obtain raw scryfall information, from cache or by query
    if name in scryfall_cache:
        print('Using cached')
        scryfall_card_data = scryfall_cache[name]
    else:
        time.sleep(50 / 1000)  # Avoid overloading Scryfall API
        scryfall_card_data = make_scryfall_request(name)
        scryfall_cache[name] = scryfall_card_data

    # Filter query to only cards exactly matching name
    scryfall_card_data = [card for card in scryfall_card_data
                          if card['name'] == name]

    # No matches, create empty card
    if (len(scryfall_card_data) == 0 or
            ('error' in scryfall_card_data[0] and
             scryfall_card_data[0]['error'])):
        return {'name': name, 'image_urls': [], 'released': -1,
                'color_identities': '', 'legal_in_mainboard': False,
                'legal_as_commander': False, 'needsUpdate': False,
                'error': True}

    # Return dictionary with card information
    return {'name': name, 'image_urls': choose_image(scryfall_card_data),
            'released': posix_time(scryfall_card_data[0]['released_at']),
            'color_identities': ''.join(scryfall_card_data[0]['color_identity']),
            'legal_in_mainboard': legal_in_main(scryfall_card_data),
            'legal_as_commander': legal_as_commander(scryfall_card_data),
            'type_line': scryfall_card_data[0]['type_line'],
            'mana_value': scryfall_card_data[0]['cmc'],
            'needsUpdate': False}


def choose_image(card_data: list[dict]) -> list[str]:
    """
    Given a list of card objects from Scryfall for a single card, select the
    best one for use in PDHREC according to a variety of factors.

    :param card_data: A list of card objects from Scryfall
    :return: a list of urls for the image.
    """
    card_data.sort(key=card_sort_key, reverse=False)
    if 'image_uris' in card_data[0]:  # Single sided
        return [card_data[0]['image_uris']['large']]
    # Double sided
    return [card_data[0]['card_faces'][0]['image_uris']['large'],
            card_data[0]['card_faces'][1]['image_uris']['large']]


def card_sort_key(printing: dict) -> tuple:
    """
    A custom sorting function to order the priority features for card images.
    Priorities (high to low): not content warning, English language, not
    digital card, high resolution, large image, has text, has black border,
    has modern frame, not a promo, no frame effects, not a secret layer, newest.

    :param printing: Scryfall printing data for a single print of a card
    :return: A tuple of integers and floats, with smaller numbers
    representing preferred printings.
    """
    content_warning = int('content_warning' in printing and printing['content_warning'])
    language = int(not ('lang' in printing and printing['lang'] == 'en'))
    digital = int(printing['digital'])

    # High res > low res > Anything else
    if printing['image_status'] == 'highres_scan':
        img_status = 0
    elif printing['image_status'] == 'lowres':
        img_status = 1
    else:
        img_status = 2

    # Size for single face cards
    if 'image_uris' in printing:
        has_large = int('large' not in printing['image_uris'])
    else:  # Double faced cards
        has_large = int('large' not in printing['card_faces'][0]['image_uris'])

    textless = int(printing['textless'])
    border_color = int(printing['border_color'] != 'black')
    frame = ['2015', 'future', '2003', '1997', '1993'].index(printing['frame'])
    promo = int(printing['promo'])

    if 'frame_effects' in printing:
        num_effects = len([effect for effect in printing['frame_effects']
                           if effect != 'snow'])
    else:
        num_effects = 0

    secret_lair = int(printing['set'] == 'sld')
    date = -posix_time(printing['released_at'])

    triangle = int("security_stamp" in printing and printing[
        "security_stamp"] == "triangle")

    masterpiece = int(printing["set_type"] == "masterpiece")

    return (content_warning, language, digital, img_status, has_large,
            textless, border_color, secret_lair, masterpiece, promo,
            triangle, num_effects, date, frame)


def get_card_names_needing_update(most_recent_update: float) -> Optional[list]:
    """
    Queries Scryfall for the name of all cards newly released since the most
    recent update.

    :param most_recent_update: a unix timestamp representing the newest
    card's update date.
    :return: a list of card names.
    """
    sets_url = """https://api.scryfall.com/sets"""
    sets_request = requests.get(sets_url)
    if sets_request.status_code != requests.codes.ok:
        print('Request failed: Get sets to get cards needing update')
        return None
    set_data = sets_request.json()['data']
    # Sort sets from newest to oldest
    set_data = sorted(set_data,
                      key=lambda card_set: -posix_time(card_set['released_at']))

    # Find the index of the most recently released set
    most_recent_index = 0  # Index of most recently released set
    while most_recent_index < (len(set_data) - 1):
        set_release = set_data[most_recent_index]['released_at']
        # If this set was already released, break the loop
        if posix_time(set_release) < time.time():
            break
        most_recent_index += 1

    # Find the index of the most recent set during the last update
    last_update_index = most_recent_index
    while last_update_index < (len(set_data) - 1):
        set_release = set_data[last_update_index]['released_at']
        # If this set was released in the last update, break the loop
        if posix_time(set_release) < most_recent_update:
            break
        last_update_index += 1

    print(f'Sets to update: {set_data[most_recent_index:last_update_index]}')

    # Filter out art cards:
    set_data = [card_set
                for card_set in set_data[most_recent_index:last_update_index]
                if card_set['set_type'] not in ('memorabilia', 'token')]

    # If no sets need update, return early
    if len(set_data) == 0:
        return []

    query = ' or '.join([f"e:{card_set['code']}" for card_set in set_data])
    query = f'(game:paper or game:mtgo)({query})'
    sets_request = requests.get(f'https://api.scryfall.com/cards/search?q={query}')
    if sets_request.status_code != requests.codes.ok:
        print('Request failed: Get cards needing update')
        return None
    sets_request_data = sets_request.json()

    names_needing_update = []
    # Add first page of cards
    for card_data in sets_request_data['data']:
        names_needing_update.append(card_data['name'])
    # Add subsequent pages of cards
    while sets_request_data['has_more']:
        sets_request = requests.get(sets_request_data['next_page'])
        if sets_request.status_code != requests.codes.ok:
            print('Request failed: Get next page of cards needing update')
            return None
        sets_request_data = sets_request.json()
        for card_data in sets_request_data['data']:
            names_needing_update.append(card_data['name'])

    return names_needing_update


def legal_in_main(scryfall_data: list[dict]) -> bool:
    """
    Return if a card is legal in PDH mainboard.

    :param scryfall_data: Scryfall data on card, as a list of dictionaries
        each describing one printing
    :return: Card legality in mainboard
    """
    # Manual name check, as scryfall behaved weirdly before
    if scryfall_data[0]['name'] in ['Mystic Remora', 'Rhystic Study']:
        return False
    return scryfall_data[0]['legalities']['paupercommander'] == 'legal'


def legal_as_commander(scryfall_data: list[dict]) -> bool:
    """
    Return if a card is legal as a PDH commander or in a commander pair.

    :param scryfall_data: Scryfall data on card, as a list of dictionaries
        each describing one printing
    :return: Card legality as commander
    """
    try:
        # New Logic:
        for printing in scryfall_data:
            # Bad sets:
            bad_sets = ["REN", "RIN", "PSAL"]
            # Bad Cards:
            bad_cards = ['Blightbelly Rat', 'Dryad Arbor', 'Phyrexian Rager', 'Self Assembler']
            if printing['set'] not in bad_sets and printing['name'] not in bad_cards:
                if 'paper' in printing['games'] and ('Creature' in printing['type_line'] or 'Background' in printing['type_line']) and printing['rarity'] == 'uncommon' and printing['set_type'] != 'funny':
                    if 'security_stamp' in printing and 'acorn' in printing['security_stamp']:
                        continue
                    if "//" in printing['type_line']:
                        # Double sided cards:
                        # Only check first half type line.
                        temp_type_line = printing['type_line'].split("//")[0]
                        if "Creature" in temp_type_line:
                            return True
                    else:
                        return True
        return False
    except IndexError:
        print(f'Card Error: {scryfall_data}')
        return False


if __name__ == '__main__':
    # Test if the image function is working:
    # test_cards = ["Opaline Sliver"]
    # for test_card in test_cards:
    #     time.sleep(100 / 1000)
    #     # test_card_request = requests.get(
    #     #     f"https://api.scryfall.com/cards/search?q=\""
    #     #     f"{quote(test_card)}\"&order=released&dir=asc&unique=prints")
    #     # if test_card_request.status_code != requests.codes.ok:
    #     #     exit(1)
    #     test_card_data = make_scryfall_request(test_card)
    #     # test_card_data = test_card_request.json()['data']
    #     print(choose_image(test_card_data))
    #     for data in test_card_data:
    #         print(card_sort_key(data), data['scryfall_uri'])

    # Test Sets to Update function:

    result = get_card_names_needing_update(1690993022.126658)
