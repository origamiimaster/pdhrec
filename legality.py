"""
Determines if a deck is a valid or not by applying the rules of PDH.
"""
from azure_database import retrieve_color_identity
def check_rules(commander, deck: list):
    if check_color_identity(commander, deck) and check_pauper_legal(commander, deck) and check_banned_cards(commander, deck):
        return True
    return False

def check_color_identity(commander, deck: list):
    commander_color_identity = retrieve_color_identity(commander)
    for card in deck:
        card_color_identity = retrieve_color_identity(card)
        for color in card_color_identity:
            if color not in commander_color_identity:
                # Card doesn't match color identity
                return False
    return True


def check_pauper_legal(commander, deck: list):
    # Fixed enough for now.
    return True


def check_banned_cards(commander, deck: list) -> bool:
    if "Mystic Remora" in deck or "Rhystic Study" in deck:
        return False
    return True


if __name__ == "__main__":
    print("Retrieving Color Identity: Tatyova, Benthic Druid")
    print(retrieve_color_identity("Tatyova, Benthic Druid"))
