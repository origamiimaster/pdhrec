"""
Card object representing data needed for the database:
"""


class Card:
    """
    A Magic: The Gathering card.

    name: card name
    image_urls: List of URLs for Scryfall card images, to allow double-faced cards
    time_first_printed: First printing as POXIS timestamp
    color_identities: Color identity as string containing subset of 'BGRUW'
    in that order
    legal_in_mainboard: If card is mainboard (non-commander) legal in PDH
    legal_as_commander: If card is legal as commander in PDH
    """
    name: str
    image_urls: list[str]
    time_first_printed: float
    color_identities: str
    legal_in_mainboard: bool
    legal_as_commander: bool

    def __init__(self) -> None:
        # Card is potentially double sided (2 images)
        self.image_urls = []

    def to_dict(self) -> dict:
        """
        Convert to dictionary for saving to database
        """
        return {"name": self.name, "image_urls": self.image_urls,
                "released": self.time_first_printed,
                "color_identities": self.color_identities,
                "legal_in_mainboard": self.legal_in_mainboard,
                "legal_as_commander": self.legal_as_commander,
                "needsUpdate": False}
