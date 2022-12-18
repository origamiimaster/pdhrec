"""
Determines if a deck is a valid or not by applying the rules of PDH.
"""
# from azure_database import retrieve_color_identity
# def check_rules(commander, deck: list):
#     if check_color_identity(commander, deck) and check_pauper_legal(commander, deck) and check_banned_cards(commander, deck):
#         return True
#     return False
#
# def check_color_identity(commander, deck: list):
#     commander_color_identity = retrieve_color_identity(commander)
#     for card in deck:
#         card_color_identity = retrieve_color_identity(card)
#         for color in card_color_identity:
#             if color not in commander_color_identity:
#                 # Card doesn't match color identity
#                 return False
#     return True
#
#
# def check_pauper_legal(commander, deck: list):
#     # Fixed enough for now.
#     return True
#
#
# def check_banned_cards(commander, deck: list) -> bool:
#     if "Mystic Remora" in deck or "Rhystic Study" in deck:
#         return False
#     return True

def check_card_allowed_in_main(scryfall_data) -> bool:
    if scryfall_data[0]['name'] in ["Mystic Remora", "Rhystic Study"]:
        return False
    if scryfall_data[0]['legalities']['paupercommander'] == "legal":
        return True
    else:
        return False

def check_card_allowed_as_commander(scryfall_data) -> bool:
    if scryfall_data[0]['legalities']['paupercommander'] == "restricted":
        return True
    else:
        # Check if a creature, and was printed at uncommon somewhere?
        for val in scryfall_data:
            if "Creature" in val['type_line'] and val['rarity'] == "uncommon":
                return True
        return False




# if __name__ == "__main__":
#     print("Retrieving Color Identity: Tatyova, Benthic Druid")
#     print(retrieve_color_identity("Tatyova, Benthic Druid"))
