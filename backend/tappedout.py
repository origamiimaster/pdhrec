"""
Access tappedout and query decks for the database.
"""

from typing import Optional
import requests
from backend.decksource import _DeckSource


class TappedOutDeckSource(_DeckSource):
    def __init__(self) -> None:
        """
        Instantiate a TappedOut deck source client.
        """
        super().__init__()
        self.deck_api = 'http://tappedout.net/api/collection/collection:deck'
        self.latest_url = 'https://tappedout.net/api/deck/latest/pauper-edh/'

    def get_deck(self, identifier) -> Optional[dict]:
        # TODO: Accessing individual decks requires a cookie.
        # This cookie is good until Aug 28, but is there a solution to
        # authentificate requests using TappedOut account information?
        deck_cookie = {"tapped": "ofg2fd0ja549vjrlm2zhmkeq0c6n5e8f"}

        # Send a request to the API
        deck_request = requests.get(f'{self.deck_api}/{identifier}',
                                    cookies=deck_cookie)
        # Check API response status
        if deck_request.status_code != requests.codes.ok:
            print('Request failed: Get deck from tappedout with identifier '
                  f'{identifier}')
            return None

        # Convert tappedout json to the database format
        deck_data = deck_request.json()
        formatted_deck_data = TappedOutDeckSource.to_standard_format(deck_data)
        return formatted_deck_data

    def get_new_decks(self, newest_deck_time: float = None) -> list:
        if newest_deck_time is None:
            newest_deck_time = 1691118970

        # Query the list of newest PDH decks
        # TODO: This returns a limited number of decks, rather than all PDH
        # decks on TappedOut. The decks are returned by popularity, rather
        # than update date.
        latest_decks_request = requests.get(f'{self.latest_url}')
        if latest_decks_request.status_code != requests.codes.ok:
            print('Request failed: Get new TappedOut decks')
            raise Exception
        latest_decks_list = latest_decks_request.json()

        collected_decks = []
        # Iterate over the list of decks adding decks newer than the newest
        # deck in the database
        for deck in latest_decks_list:
            deck_data = self.get_deck(deck['slug'])
            if deck_data['update_date'] > newest_deck_time:
                collected_decks.append(deck_data)

        return collected_decks

    @staticmethod
    def to_standard_format(deck_data: dict) -> dict:
        """
        Convert the TappedOut deck dictionary format (eg from get_deck_data)
        to the format for database insertion

        :param deck_data: TappedOut deck data, as a dictionary
        :return: Dictionary with same information in database format
        """
        mainboard = []
        commanders = []
        for card in deck_data['inventory']:
            cardname = card[0]
            # Commander cards have 'cmdr' key with value True
            if 'cmdr' in card[1] and card[1]['cmdr'] and card[1]['b'] == 'main':
                for _ in range(card[1]['qty']):
                    commanders.append(cardname)
            # Only add cards in the mainboard
            elif card[1]['b'] == 'main':
                for _ in range(card[1]['qty']):
                    mainboard.append(cardname)

        return {'_id': f"tappedout:{deck_data['slug']}",
                'update_date': deck_data['date_updated'],
                'commanders': commanders, 'cards': mainboard,
                'source': 'tappedout'}
