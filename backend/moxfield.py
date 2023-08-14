"""
Access moxfield and query decks for inclusion in the database.
"""

from typing import Optional
import requests
from time import sleep
from backend.utils import posix_time
from backend.decksource import _DeckSource


def moxfield_to_standard_format(deck_data: dict) -> dict:
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
    return {'_id': f"moxfield:{deck_data['publicId']}",
            'update_date': posix_time(deck_data['lastUpdatedAtUtc']),
            'commanders': commanders, 'cards': mainboard, 'source': "moxfield"}


class MoxfieldDeckSource(_DeckSource):
    def __init__(self) -> None:
        """
        Instantiates a moxfield deck source client.
        """
        super().__init__()
        self.api_url = "https://api.moxfield.com/v2/"

    def get_deck(self, identifier) -> Optional[dict]:
        # Send a get request to the moxfield decks API.
        request = requests.get(self.api_url + f'decks/all/{identifier}')
        # Check if the API responded successfully
        if request.status_code != requests.codes.ok:
            print(f"Request failed: Get deck from Moxfield with identifier "
                  f"{identifier}")
            return None
        # Convert the deck data to our database format:
        deck_data = request.json()
        formatted_deck_data = moxfield_to_standard_format(deck_data)
        # Return the deck data.
        return formatted_deck_data

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

        while all((posix_time(deck['lastUpdatedAtUtc']) > newest_deck_time)
                  for deck in paged_decks):
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


if __name__ == '__main__':
    expected = {
        '_id': 'yH7w5QHvCEKJSjdnrzr1EQ', 'update_date': 1691549744.723,
        'commanders': [], 'cards': []}
    source = MoxfieldDeckSource()
    print(source.get_deck('yH7w5QHvCEKJSjdnrzr1EQ') == expected)
