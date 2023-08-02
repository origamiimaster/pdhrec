"""
Determine if a deck is a valid or not by applying the rules of PDH.
"""

from backend.utils import (partner_commanders, partner_pairs,
                           background_commanders, backgrounds)


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


def pair_legal_as_commander(cardname1: str, cardname2: str) -> bool:
    """
    Provided a pair of cards both legal as commanders, return whether their
    combination is a legal commander pairing.
    """
    return (({cardname1, cardname2} in partner_pairs) or  # Partners
            (cardname1 in partner_commanders and
             cardname2 in partner_commanders and
             cardname1 != cardname2) or  # Parner with commanders
            (cardname1 in background_commanders and
             cardname2 in backgrounds) or  # Background commander, Background
            (cardname2 in background_commanders and
             cardname1 in backgrounds))  # Background, Background commander


def check_legality(deck, cards_cache, database) -> bool:
    """
    Check the legality of a deck for pauper commander:
    1. Either 1 or 2 legal uncommon commanders
    2. 99 or 98 other singleton legal common cards within the commander's
        color identity
    """
    # Check number of commanders
    if not (len(deck['commanders']) == 1 or len(deck['commanders']) == 2):
        print(f"Wrong number of commanders: {len(deck['commanders'])}")
        return False

    # Determine individual commander legalities and deck's color identities
    deck_color_identity = set()
    for commander in deck['commanders']:
        if commander not in cards_cache:  # Update cache if needed
            cards_cache[commander] = database.get_card(commander)
        if cards_cache[commander] is None:  # Commander missing from database
            print(f"Missing commander from database: {commander}")
            database.insert_card({"name": commander, "needsUpdate": True})
            return False
        if not cards_cache[commander]['legal_as_commander']:  # Illegal commander
            print(f"Illegal Commander: {commander}")
            return False
        # Update deck color identities with commander's color identity
        deck_color_identity.update(set(cards_cache[commander]['color_identities']))

    # Verify legal commander pair
    if (len(deck['commanders']) == 2 and
            not pair_legal_as_commander(deck['commanders'][0],
                                        deck['commanders'][1])):
        print(f"Illegal Commander pair: {deck['commanders'][0]} with {deck['commanders'][1]}")
        return False

    # Determine legality of other cards
    # TODO: Does this check if there are the correct number of cards?
    for card in deck['cards']:
        if card not in cards_cache:  # Update cache if needed
            cards_cache[card] = database.get_card(card)
        if cards_cache[card] is None:  # Card missing from database
            print(f"Missing card from database {card}")
            return False
        if not cards_cache[card]['legal_in_mainboard']:  # Illegal card
            print(f"Illegal card: {card}")
            return False
        if not all(color in deck_color_identity  # Check color identity
                   for color in cards_cache[card]['color_identities']):
            print(f"Illegal color identities: {card}, {deck['commanders']}")
            return False

    # If commanders and cards are legal, the deck is legal
    return True
