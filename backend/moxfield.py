"""
Access moxfield and query decks for inclusion in the database.
"""

from typing import Optional
import requests
from time import sleep, time
from backend.database import MongoDatabase
from backend.utils import posix_time
from backend.decksource import DeckSource


class MoxfieldDeckSource(DeckSource):
    def __init__(self) -> None:
        """
        Instantiates a moxfield deck source client.
        """
        super().__init__()
        self.api_url = "https://api.moxfield.com/v2/"

    def get_deck(self, identifier) -> Optional[dict]:
        # Send a get request to the moxfield decks API.
        request = requests.get(self.api_url + f"decks/all/{identifier}")
        # Check if the API responsed successfully
        if request.status_code != requests.codes.ok:
            print(f"Request failed: Get deck from Moxfield with identifier "
                  f"{identifier}")
            return None
        # Convert the deck data to our database format:
        deck_data = request.json()
        formatted_deck_data = self.convert_to_standard_format(deck_data)
        # Return the deck data.
        return formatted_deck_data

    def convert_to_standard_format(self, deck_data: dict) -> dict:
        """
        Convert the Moxfield deck dictionary format (eg from get_deck_data)
        to the format for database insertion

        :param deck_data: Moxfield deck data, as a dictionary
        :return: Dictionary with same information in database format
        """
        mainboard = []
        for card_name in deck_data['mainboard']:
            for _ in range(deck_data['mainboard'][card_name]['quantity']):
                mainboard.append(card_name)
        commanders = [commander_name for commander_name in
                      deck_data['commanders']]
        return {'_id': deck_data['publicId'],
                'update_date': posix_time(deck_data['lastUpdatedAtUtc']),
                'commanders': commanders,
                'cards': mainboard}

    def get_new_decks(self, newest_deck_time: float = None) -> list:
        if newest_deck_time is None:
            # There is no limit to the search, not yet supported?
            # Use a fixed stop time instead:
            newest_deck_time = 1691118970

        collected_deck_ids = []

        index = 1
        paged_decks = self.get_new_decks_paginated(index)
        if paged_decks is None:
            raise ValueError

        while all([posix_time(x['lastUpdatedAtUtc']) > newest_deck_time for x
                   in paged_decks]):
            for deck in paged_decks:
                collected_deck_ids.append(deck['publicId'])

            index += 1
            paged_decks = self.get_new_decks_paginated(index)
            if paged_decks is None:
                raise ValueError
            sleep(0.5)

        for deck in paged_decks:
            if posix_time(deck['lastUpdatedAtUtc']) <= newest_deck_time:
                break
            collected_deck_ids.append(deck['publicId'])

        collected_decks = []
        for deck_id in collected_deck_ids:
            collected_decks.append(self.get_deck(deck_id))

        return collected_decks

    def get_new_decks_paginated(self, page: int = 1) -> Optional[list[dict]]:
        """
        Query the given page in the moxfield list of new decks (in reverse
        chronological order). If page not given, return the first page.

        :param page: Page of the list of new decks to return
        :return: metadata on most recent decks, as list of dictionaries
        """
        url = f"""{self.api_url}decks/search?pageNumber={page}&pageSize=64&sortType=updated&sortDirection=Descending&fmt=pauperEdh&board=mainboard"""
        decks_request = requests.get(url)
        if decks_request.status_code != requests.codes.ok:
            print(f'Request failed: Get new decks: page {page}')
            return None
        return decks_request.json()['data']


def get_deck_data(deck_id: str) -> Optional[dict]:
    """
    Query moxfield for a deck's information given the deck ID.

    :param deck_id: Deck ID on Moxfield
    :return: Return the deck information as a dictionary if found.
    Otherwise, return None.
    """
    url = f"https://api.moxfield.com/v2/decks/all/{deck_id}"
    deck_request = requests.get(url)
    if deck_request.status_code != requests.codes.ok:
        print(f"Request failed: Get deck data from Moxfield: {deck_id}")
        return None
    return deck_request.json()


def get_new_decks(page: int = 1) -> Optional[list[dict]]:
    """
    Query the given page in the moxfield list of new decks (in reverse
    chronological order). If page not given, return the first page.

    :param page: Page of the list of new decks to return
    :return: metadata on most recent decks, as list of dictionaries
    """
    url = f"""https://api.moxfield.com/v2/decks/search?pageNumber={page}&pageSize=64&sortType=updated&sortDirection=Descending&fmt=pauperEdh&board=mainboard"""
    decks_request = requests.get(url)
    if decks_request.status_code != requests.codes.ok:
        print(f'Request failed: Get new decks: page {page}')
        return None
    return decks_request.json()['data']


def convert_for_database(moxfield_deck_data: dict) -> dict:
    """
    Convert the Moxfield deck dictionary format (eg from get_deck_data)
    to the format for database insertion

    :param moxfield_deck_data: Moxfield deck data, as a dictionary
    :return: Dictionary with same information in database format
    """
    mainboard = []
    for card_name in moxfield_deck_data['mainboard']:
        for _ in range(moxfield_deck_data['mainboard'][card_name]['quantity']):
            mainboard.append(card_name)
    commanders = [commander_name for commander_name in
                  moxfield_deck_data['commanders']]
    return {'_id': moxfield_deck_data['publicId'],
            'update_date': posix_time(moxfield_deck_data['lastUpdatedAtUtc']),
            'commanders': commanders,
            'cards': mainboard}


def add_moxfield_decks_to_database(database: MongoDatabase) -> bool:
    """
    Add new decks on Moxfield to the database. Query Moxfield for the list of
    all PDH decks, then iterate backwards in time over this list (updating the
    database) until the most recent deck in the database is found.

    :param database: Database object containing all deck and card information
    :return: Status of updating decks from Moxfield
    """
    print('Auto updating decks to database')
    latest_updated_deck = database.decks.find_one(sort=[('update_date', -1)])
    if latest_updated_deck is None:  # If database starts empty
        latest_updated_time = 1691118970.0622232
    else:
        latest_updated_time = latest_updated_deck['update_date']
    new_decks = get_new_decks(1)  # Page 1 of all decks
    if new_decks is None:  # Catch request error
        return False
    newest_deck = new_decks[0]
    newest_time = posix_time(newest_deck['lastUpdatedAtUtc'])

    print('Updating decks')
    curr_deck_time = newest_time
    curr_page = 1  # Results are paginated
    # Update decks in reverse chronological order until last updated deck
    while latest_updated_time < curr_deck_time:
        for deck in new_decks:
            # Last updated deck found, break
            if latest_updated_time >= curr_deck_time:
                break

            # Save the new deck to the database
            print(f"Saving deck {deck['name']}")
            queried_deck_data = get_deck_data(deck['publicId'])
            if queried_deck_data is None:  # Catch request error
                print(f"Deck skipped: {deck['name']}")
                continue
            deck_obj = convert_for_database(queried_deck_data)
            deck_obj['needsLegalityCheck'] = True
            database.insert_deck(deck_obj)

            # Update curr_deck_time and break if older than
            curr_deck_time = deck_obj['update_date']
        # Wait for 1 second to respect APIs
        sleep(1)
        # Page fully processed so progress to next page
        curr_page += 1
        new_decks = get_new_decks(curr_page)
        if new_decks is None:  # Catch request error
            return False
    return True


if __name__ == '__main__':
    test_deck = get_deck_data('LXiuz3D1DkO8m4mxBKVNGg')
    parsed = convert_for_database(test_deck)
    source = MoxfieldDeckSource()
    print(source.get_deck('LXiuz3D1DkO8m4mxBKVNGg') == parsed)
    decks = source.get_new_decks(1691440000)
    print(len(decks))
    assert all([x['update_date'] > 1691440000 for x in decks])
