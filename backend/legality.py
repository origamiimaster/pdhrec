"""
Determines if a deck is a valid or not by applying the rules of PDH.
"""

def check_card_allowed_in_main(scryfall_data) -> bool:
    if scryfall_data[0]['name'] in ["Mystic Remora", "Rhystic Study"]:
        return False
    if scryfall_data[0]['legalities']['paupercommander'] == "legal":
        return True
    else:
        return False

def check_card_allowed_as_commander(scryfall_data) -> bool:
    try:
        if scryfall_data[0]['legalities']['paupercommander'] == "restricted":
            return True
        elif scryfall_data[0]['legalities']['paupercommander'] == "not_legal":
            return False
        else:
            # Check if a creature, and was printed at uncommon somewhere?
            for val in scryfall_data:
                if "paper" in val["games"] and "Creature" in val['type_line'] and val['rarity'] == "uncommon":
                    return True
            return False
    except IndexError:
        print(f"Card Errored Out: {scryfall_data}")
        return False




# if __name__ == "__main__":
#     print("Retrieving Color Identity: Tatyova, Benthic Druid")
#     print(retrieve_color_identity("Tatyova, Benthic Druid"))
