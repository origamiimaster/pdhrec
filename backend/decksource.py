"""
A deck source represents a collection of decks, like moxfield / archidekt.
"""
from typing import Optional


class _DeckSource:
    """
    A source for deck data.
    Examples include Moxfield.com, Archidekt.com, ...
    """
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    def get_deck(self, identifier) -> Optional[dict]:
        """
        Gets a particular deck from the source.
        :param identifier: A public ID for the deck requested.
        :return: The deck object.
        """
        raise NotImplementedError

    def get_new_decks(self, newest_deck_time: float = None) -> list:
        """
        Returns a set of new decks from the source that are newer than
        parameter newest_deck_time.
        :param newest_deck_time: A unix timestamp for the most recent deck.
        :return:
        """
        raise NotImplementedError
