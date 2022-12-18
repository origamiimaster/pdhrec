"""
Defines the deck object that is stored and returned by the database.
"""
import time
import typing


class Deck:
    """
    A Pauper Commander Deck.  Describes the contents of the deck, at a particular time.

    Cards are referenced by their card id, which will be unique per card?
    """
    commanders: typing.List[str]
    main_board: typing.List[str]
    last_updated: int
    id: str

    def __init__(self) -> None:
        self.commanders = []
        self.main_board = []

    def to_dict(self) -> dict:
        """Converts to dictionary representation"""
        return {"_id": self.id, "update_date": self.last_updated,
                "commanders": self.commanders, "cards": self.main_board}

if __name__ == "__main__":
    print("Generating default test deck")
    my_deck = Deck()
    my_deck.commander = ["Murmuring Mystic"]
    my_deck.main_board = ["Island" for _ in range(99)]
    my_deck.last_updated = time.time()
    my_deck.id = "default_deck_id"
