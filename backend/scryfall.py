"""
Accessing Scryfall for card images.
"""

import gzip
from typing import Optional
import time
import json
import re
import requests
from urllib.parse import quote
from threading import Lock
from time import sleep, monotonic
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from collections import defaultdict

from backend.utils import posix_time
import tqdm


ALL_PAUPER_COMMANDERS = None


def normalize_name(name: str) -> str:
    """
    Normalize a card name for matching purposes.

    A small number of joke/Un-set cards use runs of underscores as a
    "fill in the blank" placeholder in their printed name (e.g. Scryfall's
    canonical "________ Goblin", 8 underscores). Deck-building sites often
    store a different, fixed-length placeholder for these cards (e.g.
    "_____ Goblin", 5 underscores) rather than reproducing Scryfall's exact
    name, which breaks a strict string equality check. Collapsing any run
    of underscores down to a single one makes matching tolerant of this
    without meaningfully risking false-positive matches, since essentially
    no other real card name contains an underscore at all.

    :param name: a card name, from either Scryfall or another source
    :return: the name with any run of underscores collapsed to one
    """
    return re.sub(r'_+', '_', name)


class ScryfallClient:
    """
    Wrapper around Scryfall requests.

    Handles:
      - request throttling
      - Retry-After headers
      - exponential backoff

    NOTE: With bulk-data-backed lookups (see build_scryfall_index /
    get_card_from_scryfall below), this client is now only exercised for:
      - the small number of cards not found in the bulk index (fallback)
      - get_card_names_needing_update (set + search queries, not per-card)
      - get_all_paupercommanders (one paginated search, not per-card)
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "PDHREC/1.0",
            "Accept": "*/*"
        }

        # Scryfall recommends <= 10 requests/sec.
        # This gives us 5/sec and avoids burst limits.
        self.min_interval = 0.2

        self.last_request = 0.0
        self.lock = Lock()

    def throttle(self):
        with self.lock:
            elapsed = monotonic() - self.last_request

            if elapsed < self.min_interval:
                sleep(self.min_interval - elapsed)

            self.last_request = monotonic()

    def get(self, url):
        """
        GET request with automatic retry handling.
        """

        max_retries = 8

        for attempt in range(max_retries):
            self.throttle()

            response = requests.get(
                url,
                headers=self.headers
            )

            if response.status_code == requests.codes.ok:
                return response

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    try:
                        # Seconds
                        wait = float(retry_after)

                    except ValueError:
                        # HTTP date
                        retry_time = parsedate_to_datetime(retry_after)

                        if retry_time.tzinfo is None:
                            retry_time = retry_time.replace(
                                tzinfo=timezone.utc
                            )

                        wait = (
                            retry_time -
                            datetime.now(timezone.utc)
                        ).total_seconds()

                    wait = max(wait, 1)

                else:
                    # Exponential backoff
                    wait = min(2 ** attempt, 60)

                tqdm.tqdm.write(
                    f"Scryfall rate limited. "
                    f"Waiting {wait:.1f}s"
                )

                sleep(wait)
                continue

            return response

        raise RuntimeError(
            "Scryfall request failed after maximum retries"
        )


scryfall_client = ScryfallClient()


# ---------------------------------------------------------------------------
# Bulk data indexing
# ---------------------------------------------------------------------------

def build_scryfall_index(bulk_filepath: str) -> dict[str, list[dict]]:
    """
    Load a Scryfall bulk data file (e.g. from get_latest_bulk_file, using the
    'default_cards' bulk type) and index it by card name.

    Use 'default_cards', not 'oracle_cards', for this file. 'oracle_cards'
    collapses each card down to a single printing, which breaks choose_image's
    ranking logic (it expects multiple printings to compare and pick the best
    image from). 'default_cards' keeps (roughly) one printing per set, which
    is what card_sort_key is designed to sort through.

    :param bulk_filepath: path to a downloaded Scryfall bulk data JSON file
    :return: dict mapping card name -> list of printing dicts, matching the
        shape previously returned per-name by make_scryfall_request
    """
    tqdm.tqdm.write(f'Loading bulk data from {bulk_filepath}')

    with gzip.open(bulk_filepath, 'r') as bulk_file:
        # Todo: figure out how to add encoding='utf-8', and hope this works
        bulk_cards = [json.loads(line) for line in bulk_file if line.strip()]

    index = defaultdict(list)
    for card in bulk_cards:
        index[normalize_name(card['name'])].append(card)

        # Double-faced cards are indexed under the combined "Front // Back"
        # name by Scryfall. Also index by each individual face name so
        # lookups by a single face name still resolve.
        if 'card_faces' in card and 'name' not in card.get('image_uris', {}):
            for face in card['card_faces']:
                if 'name' in face and face['name'] != card['name']:
                    index[normalize_name(face['name'])].append(card)

    tqdm.tqdm.write(f'Indexed {len(index)} unique card names')
    return index


def make_scryfall_request(name) -> list:
    """
    Fallback path: query the live Scryfall API for a single card name.

    This is now only used when a card can't be found in the bulk data index
    (e.g. it was released after the bulk file was generated). Prefer
    get_card_from_scryfall with a card_index built via build_scryfall_index.
    """
    tqdm.tqdm.write('Searching')

    url = (
        "https://api.scryfall.com/cards/search?"
        f'q="{quote(name)}"'
        "&order=released"
        "&dir=asc"
        "&unique=prints"
    )

    card_request = scryfall_client.get(url)

    if card_request.status_code != requests.codes.ok:
        print(f'Request failed: Get card from Scryfall: {name}')
        return [{
            'name': name,
            'image_urls': [],
            'released': -1,
            'color_identities': '',
            'legal_in_mainboard': False,
            'legal_as_commander': False,
            'needsUpdate': False,
            'error': True
        }]

    scryfall_card_data = []

    resp_data = card_request.json()

    scryfall_card_data += resp_data['data']

    while resp_data["has_more"]:
        card_request = scryfall_client.get(
            resp_data["next_page"]
        )

        if card_request.status_code != requests.codes.ok:
            print(f'Request failed: Get card from Scryfall: {name}')
            return [{
                'name': name,
                'image_urls': [],
                'released': -1,
                'color_identities': '',
                'legal_in_mainboard': False,
                'legal_as_commander': False,
                'needsUpdate': False,
                'error': True
            }]

        resp_data = card_request.json()
        scryfall_card_data += resp_data['data']
    return scryfall_card_data


def get_card_from_scryfall(
    name: str,
    card_index: Optional[dict] = None,
    scryfall_cache: Optional[dict] = None
) -> dict:
    """
    Query and return card data for a single card, preferring the local bulk
    data index and only falling back to a live API request if the card isn't
    found there.

    :param name: Card name to query
    :param card_index: Bulk-data index built by build_scryfall_index, mapping
        name -> list of printings. Pass None to skip straight to live
        requests (old behavior).
    :param scryfall_cache: Cache of cards previously queried live on
        Scryfall, used only for the fallback path. Populated in place.
    :return: Dictionary with Scryfall data for database insertion
    """
    scryfall_card_data = None

    # Prefer the bulk index -- no network request required.
    if card_index is not None and name in card_index:
        scryfall_card_data = card_index[name]

    # Fall back to a live request for cards missing from the bulk snapshot
    # (e.g. brand new releases not yet in that day's bulk data).
    if not scryfall_card_data:
        if scryfall_cache is None:
            scryfall_cache = {}

        if name in scryfall_cache:
            scryfall_card_data = scryfall_cache[name]
        else:
            tqdm.tqdm.write(f'{name} not found in bulk index, querying live')
            scryfall_card_data = make_scryfall_request(name)
            scryfall_cache[name] = scryfall_card_data

    scryfall_card_data = [
        card for card in scryfall_card_data
        if normalize_name(card['name']) == normalize_name(name)
    ]

    # No matches, create empty card
    if (
            len(scryfall_card_data) == 0
            or (
                'error' in scryfall_card_data[0]
                and scryfall_card_data[0]['error']
            )
    ):
        return {
            'name': name,
            'image_urls': [],
            'released': -1,
            'color_identities': '',
            'legal_in_mainboard': False,
            'legal_as_commander': False,
            'needsUpdate': False,
            'error': True
        }

    # Return dictionary with card information
    return {
        'name': name,
        'image_urls': choose_image(scryfall_card_data),
        'released': posix_time(
            scryfall_card_data[0]['released_at']
        ),
        'color_identities': ''.join(
            scryfall_card_data[0]['color_identity']
        ),
        'legal_in_mainboard': legal_in_main(scryfall_card_data),
        'legal_as_commander': legal_as_commander(scryfall_card_data),
        'type_line': scryfall_card_data[0]['type_line'],
        'mana_value': scryfall_card_data[0]['cmc'],
        'needsUpdate': False
    }


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
    content_warning = int(
        'content_warning' in printing and printing['content_warning'])
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
    sets_request = scryfall_client.get(sets_url)
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
    sets_request = scryfall_client.get(f'https://api.scryfall.com/cards/search?q={query}')
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
        sets_request = scryfall_client.get(sets_request_data['next_page'])
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

    Checks every printing rather than just scryfall_data[0]. Scryfall's
    per-printing 'legalities' value is not always uniform across a card's
    printings (e.g. art-series objects, oversized cards, and some
    promo/serialized treatments carry their own 'not_legal' status even when
    the same card has a legal printing elsewhere). choose_image() also sorts
    this same list in place (for best *image*, not best *legality*) before
    this function typically gets called, so relying on index 0 here would
    pick up whatever printing happened to win the image ranking rather than
    reflecting the card's actual legality. A card is legal in mainboard if
    ANY printing is legal.

    :param scryfall_data: Scryfall data on card, as a list of dictionaries
        each describing one printing
    :return: Card legality in mainboard
    """
    # Manual name check, as scryfall behaved weirdly before
    if scryfall_data[0]['name'] in ['Mystic Remora', 'Rhystic Study']:
        return False
    return any(
        printing.get('legalities', {}).get('paupercommander') == 'legal'
        for printing in scryfall_data
    )


def legal_as_commander(scryfall_data: list[dict]) -> bool:
    """
    Return if a card is legal as a PDH commander or in a commander pair.

    :param scryfall_data: Scryfall data on card, as a list of dictionaries
        each describing one printing
    :return: Card legality as commander
    """
    name = scryfall_data[0]['name']
    global ALL_PAUPER_COMMANDERS
    if ALL_PAUPER_COMMANDERS is None:
        ALL_PAUPER_COMMANDERS = get_all_paupercommanders()

    return name in ALL_PAUPER_COMMANDERS


def get_all_paupercommanders():
    print("Called get_all_paupercommanders")
    r = scryfall_client.get(
        'https://api.scryfall.com/cards/search?q=is:pauperCommander'
    )
    if r.status_code != 200:
        print("Error pulling commanders")
        print(f"Error status code {r.status_code}")
        return None
    names = [x['name'] for x in r.json()['data']]
    while r.json()['has_more']:
        r = scryfall_client.get(r.json()['next_page'])
        names += [x['name'] for x in r.json()['data']]
    return names


if __name__ == '__main__':
    test_card = "Fynn, the Fangbearer"
    test_card_data = make_scryfall_request(test_card)
    print(test_card_data)
    result = get_card_names_needing_update(1690993022.126658)
