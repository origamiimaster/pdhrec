"""
Defines the deck object that is stored and returned by the database.
"""
import time


class Deck:
    """
    A Pauper Commander Deck.

    commander: list of commanders in the deck, by name.
    main_board: list of mainboard cards in the deck, by name.
    last_updated: last update time as POSIX time
    id: Deck ID on Moxfield
    """
    commanders: list[str]
    main_board: list[str]
    last_updated: float
    id: str

    def __init__(self) -> None:
        self.commanders = []
        self.main_board = []

    def to_dict(self) -> dict:
        """
        :return: A dictionary representation for saving to database.
        """
        return {"_id": self.id, "update_date": self.last_updated,
                "commanders": self.commanders, "cards": self.main_board}


if __name__ == "__main__":
    print("Generating default test deck")
    my_deck = Deck()
    my_deck.commander = ["Murmuring Mystic"]
    my_deck.main_board = ["Island" for _ in range(99)]
    my_deck.last_updated = time.time()
    my_deck.id = "default_deck_id"
