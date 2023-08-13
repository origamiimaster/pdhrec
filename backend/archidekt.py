"""
Access moxfield and query decks for inclusion in the database.
"""
from typing import Optional

import requests
from time import sleep
from backend.decksource import DeckSource
from backend.utils import posix_time


class ArchidektDeckSource(DeckSource):
    def __init__(self) -> None:
        """
        Instantiates an archidekt deck source client.
        """
        super().__init__()
        self.api_url = "https://archidekt.com/api/decks/"
        self.name = "moxfield"

    def get_deck(self, identifier) -> Optional[dict]:
        # Send a get request to the archidekt decks API.
        request = requests.get(self.api_url + f"{identifier}/?format=json")

        # Check if the API responded successfully
        if request.status_code != requests.codes.ok:
            if request.status_code == requests.codes.too_many_requests:
                delay = 30
                print(f"Request ratelimited for deck {identifier}, retrying in"
                      f" {delay} seconds.")
                sleep(delay)
                return self.get_deck(identifier)
            print(f"Request failed: Get deck from Archidekt with identifier "
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
        commanders = []
        for card in deck_data['cards']:
            if "Commander" in card['categories']:
                commanders.append(card['card']['oracleCard']['name'])
            else:
                mainboard.append(card['card']['oracleCard']['name'])

        return {
            '_id': "archidekt:" + str(deck_data['id']),
            'update_date': posix_time(deck_data['updatedAt']),
            'commanders': commanders, 'cards': mainboard, 'source': "archidekt"
                }

    def get_new_decks(self, newest_deck_time: float = None) -> list:
        if newest_deck_time is None:
            newest_deck_time = -1

        collected_deck_ids = []

        index = 1
        paged_decks = self.get_new_decks_paginated(index)
        if paged_decks is None:
            raise ValueError

        while (all([posix_time(x['updatedAt']) > newest_deck_time for x
                   in paged_decks["results"]]) and paged_decks['next'] is not
               None):
            for deck in paged_decks["results"]:
                collected_deck_ids.append(deck['id'])

            index += 1
            paged_decks = self.get_new_decks_paginated(index)

            if paged_decks is None:
                raise ValueError
            sleep(0.5)

        for deck in paged_decks["results"]:
            if posix_time(deck['updatedAt']) <= newest_deck_time:
                break
            collected_deck_ids.append(deck['id'])

        collected_decks = []
        for deck_id in collected_deck_ids:
            collected_decks.append(self.get_deck(deck_id))
            sleep(1.0)

        return collected_decks

    def get_new_decks_paginated(self, page: int = 1) -> Optional[dict]:
        """
        Query the given page in the moxfield list of new decks (in reverse
        chronological order). If page not given, return the first page.

        :param page: Page of the list of new decks to return
        :return: metadata on most recent decks, as list of dictionaries
        """
        url = self.api_url + f"?formats=17&orderBy=-updatedAt&page={page}"
        decks_request = requests.get(url)
        if decks_request.status_code != requests.codes.ok:
            print(f'Request failed: Get new decks: page {page}')
            return None
        return decks_request.json()


if __name__ == "__main__":
    source = ArchidektDeckSource()
    temp = source.get_deck('5018222')
    print(temp)
    temp = source.get_new_decks(newest_deck_time=1691750188.0)
    print(len(temp))
