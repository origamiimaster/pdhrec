"""
Determine if a deck is a valid or not by applying the rules of PDH.
"""

def card_legal_in_main(scryfall_data) -> bool:
    # Manual name check, as scryfall behaved weirdly before
    if scryfall_data[0]['name'] in ["Mystic Remora", "Rhystic Study"]:
        return False 
    return scryfall_data[0]['legalities']['paupercommander'] == "legal"


def card_legal_as_commander(scryfall_data) -> bool:
    try:
        if scryfall_data[0]['legalities']['paupercommander'] == "restricted":
            return True
        elif scryfall_data[0]['legalities']['paupercommander'] == "not_legal":
            return False
        else:
            # Check if a creature printed common at some point
            for printing in scryfall_data:
                if ("paper" in printing["games"] and 
                    "Creature" in printing['type_line'] and 
                    printing['rarity'] == "uncommon"):
                    return True
            return False
    except IndexError:
        print(f"Card Error: {scryfall_data}")
        return False




# if __name__ == "__main__":
#     print("Retrieving Color Identity: Tatyova, Benthic Druid")
#     print(retrieve_color_identity("Tatyova, Benthic Druid"))
