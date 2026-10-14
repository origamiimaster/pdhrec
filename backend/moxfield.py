"""
Access moxfield and query decks for inclusion in the database.
"""

from typing import Optional
import requests
import cloudscraper

from threading import Lock
from time import sleep, monotonic
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

from backend.utils import posix_time
from backend.decksource import _DeckSource


class MoxfieldDeckSource(_DeckSource):
    def __init__(self) -> None:
        """
        Instantiates a moxfield deck source client.
        """
        super().__init__('moxfield')
        self.api_url = 'https://api.moxfield.com/v2/'
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/114.0.0.0 Mobile Safari/537.36",
        }
        self.scraper = cloudscraper.create_scraper()

        # ----- Rate limiting -----

        # Minimum time between requests (seconds).
        # 0.5 = 2 requests/sec.
        self._min_interval = 0.5

        self._last_request = 0.0
        self._request_lock = Lock()

    def _throttle(self):
        """Ensure requests are not sent faster than the configured rate.
        Probably unnecessary but you never know with threads
        """
        with self._request_lock:
            elapsed = monotonic() - self._last_request

            if elapsed < self._min_interval:
                sleep(self._min_interval - elapsed)

            self._last_request = monotonic()

    def _get(self, url: str, **kwargs):
        """
        Perform a GET request with:
          - proactive throttling
          - automatic Retry-After handling
          - exponential backoff fallback
        """
        max_retries = 8

        for attempt in range(max_retries):
            self._throttle()

            response = self.scraper.get(url, **kwargs)

            if response.status_code == requests.codes.ok:
                return response

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    try:
                        # Retry-After specified as seconds
                        wait = float(retry_after)
                    except ValueError:
                        # Retry-After specified as an HTTP date
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

                print(
                    f"Rate limited (429). "
                    f"Retrying in {wait:.1f} seconds..."
                )

                sleep(wait)
                continue

            return response

        raise RuntimeError("Exceeded maximum retries.")

    def get_deck(self, identifier) -> Optional[dict]:
        # Send a get request to the moxfield decks API.
        response = self._get(self.api_url + f'decks/all/{identifier}')
        # Check if the API responded successfully
        if response.status_code != requests.codes.ok:
            print(f"Request failed: Get deck from Moxfield with identifier "
                  f"{identifier}")
            print(f"status code: {response.status_code}")
            return None
        # Convert the deck data to our database format:
        deck_data = response.json()
        formatted_deck_data = MoxfieldDeckSource.to_standard_format(deck_data)
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

        for deck in paged_decks:
            if posix_time(deck['lastUpdatedAtUtc']) <= newest_deck_time:
                break

            collected_deck_ids.append(deck['publicId'])

        collected_decks = []
        for deck_id in collected_deck_ids:
            collected_decks.append(self.get_deck(deck_id))

        return collected_decks

    def get_new_decks_paginated(
        self,
        page: int = 1
    ) -> Optional[list[dict]]:
        """
        Query the given page in the moxfield list of new decks (in reverse
        chronological order). If page not given, return the first page.

        :param page: Page of the list of new decks to return
        :return: metadata on most recent decks, as list of dictionaries
        """
        url = f"""{self.api_url}decks/search?pageNumber={page}&pageSize=64&sortType=updated&sortDirection=Descending&fmt=pauperEdh&board=mainboard"""
        response = self._get(
            url,
            headers=self.headers
        )
        if response.status_code != requests.codes.ok:
            print(f'Request failed: Get new decks: page {page}')
            print(f"status code: {response.status_code}")
            return None
        return response.json()['data']

    @staticmethod
    def to_standard_format(deck_data: dict) -> dict:
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
                'commanders': commanders, 'cards': mainboard,
                'source': "moxfield"}


if __name__ == '__main__':
    expected = {
        '_id': 'moxfield:yH7w5QHvCEKJSjdnrzr1EQ', 'update_date': 1691549744.723,
        'commanders': [], 'cards': [], 'source': 'moxfield'}
    source = MoxfieldDeckSource()
    print(source.get_deck('yH7w5QHvCEKJSjdnrzr1EQ') == expected)
