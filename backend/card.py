"""
Card object representing data needed for the database:
"""


class Card:
    """
    A card with a particular name.
    """
    name: str
    image_urls: [str]
    time_first_printed: int
    color_identities: str
    legal_in_mainboard: bool
    legal_as_commander: bool

    def __init__(self) -> None:
        # Card is potentially double sided (2 images)
        self.image_urls = []

    def to_dict(self):
        return {"name": self.name, "image_urls": self.image_urls, "released": self.time_first_printed,
                "color_identities": self.color_identities, "legal_in_mainboard": self.legal_in_mainboard,
                "legal_as_commander": self.legal_as_commander, "needsUpdate": False}
