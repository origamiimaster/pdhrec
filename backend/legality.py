"""
Determine if a deck is a valid or not by applying the rules of PDH.
"""
from backend.database import MongoDatabase
from backend.utils import (partner_commanders, partner_pairs,
                           background_commanders, backgrounds)


def pair_legal_as_commander(commander1: str, commander2: str) -> bool:
    """
    Provided a pair of cards both legal as commanders, return whether their
    combination is a legal commander pairing.

    :param commander1: First commander
    :param commander2: Second commander
    :return: Whether the provided commanders can be legally paired
    """
    return (({commander1, commander2} in partner_pairs) or  # Partners
            (commander1 in partner_commanders and
             commander2 in partner_commanders and
             commander1 != commander2) or  # Partner with commanders
            (commander1 in background_commanders and
             commander2 in backgrounds) or  # Background commander, Background
            (commander2 in background_commanders and
             commander1 in backgrounds))  # Background, Background commander


def is_legal(deck: dict, cards_cache: dict, database: MongoDatabase) -> bool:
    """
    Check the legality of a deck for pauper commander:
    1. Either 1 or 2 legal uncommon commanders
    2. 99 or 98 other singleton legal common cards within the commander's
        color identity

    :param deck: Deck as a dictionary produced from a Deck object
    :param cards_cache: In-memory cache of card data
    :param database: MongoDatabase of card information
    :return: PDH legality of the provided deck
    """
    # Verify deck size
    if (len(deck['commanders']) + len(deck['cards'])) != 100:
        print(f"Illegal deck size: {len(deck['commanders']) + len(deck['cards'])}")
        return False

    # Verify number of commanders
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
        try:
            if not cards_cache[commander]['legal_as_commander']:  # Illegal commander
                print(f"Illegal Commander: {commander}")
                return False
        except:
            print(cards_cache[commander])
            raise Exception()
        # Update deck color identities with commander's color identity
        deck_color_identity.update(set(cards_cache[commander]['color_identities']))

    # Verify legal commander pair
    if (len(deck['commanders']) == 2 and
            not pair_legal_as_commander(deck['commanders'][0],
                                        deck['commanders'][1])):
        print(f"Illegal Commander pair: {deck['commanders'][0]} with {deck['commanders'][1]}")
        return False

    # Determine legality of mainboard cards
    for card in deck['cards']:
        if card not in cards_cache:  # Update cache if needed
            cards_cache[card] = database.get_card(card)
        if cards_cache[card] is None:  # Card missing from database
            print(f"Missing card from database {card}")
            return False
        if not cards_cache[card]['legal_in_mainboard']:  # Illegal card
            print(f"Illegal card: {card}")
            return False
        card_color_identity = set(cards_cache[card]['color_identities'])
        if not card_color_identity.issubset(deck_color_identity):
            print(f"Illegal color identities: {card}, {deck['commanders']}")
            return False

    # If commanders and cards are legal, the deck is legal
    return True
