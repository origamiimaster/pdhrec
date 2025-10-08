"""
Determine if a deck is a valid or not by applying the rules of PDH.
"""
import tqdm
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
        tqdm.tqdm.write(f"Illegal deck size:"
                        f" {len(deck['commanders']) + len(deck['cards'])}")
        return False

    # Verify number of commanders
    if not (len(deck['commanders']) == 1 or len(deck['commanders']) == 2):
        tqdm.tqdm.write(f"Wrong number of commanders:"
                        f" {len(deck['commanders'])}")
        return False

    # Determine individual commander legalities and deck's color identities
    deck_color_identity = set()
    for commander in deck['commanders']:
        if commander not in cards_cache:  # Update cache if needed
            cards_cache[commander] = database.get_card(commander)
        if cards_cache[commander] is None:  # Commander missing from database
            tqdm.tqdm.write(f'Missing commander from database: {commander}')
            database.insert_card({'name': commander, 'needsUpdate': True})
            return False
        try:
            # Illegal commander
            if not cards_cache[commander]['legal_as_commander']:
                tqdm.tqdm.write(f'Illegal Commander: {commander}')
                return False
        except Exception as e:
            print(cards_cache[commander])
            raise e
        # Update deck color identities with commander's color identity
        deck_color_identity.update(set(cards_cache[commander]['color_identities']))

    # Verify legal commander pair
    if (len(deck['commanders']) == 2 and
            not pair_legal_as_commander(deck['commanders'][0],
                                        deck['commanders'][1])):
        tqdm.tqdm.write(f"Illegal Commander pair: {deck['commanders'][0]} with"
                        f" {deck['commanders'][1]}")
        return False

    # Determine legality of mainboard cards
    for card in deck['cards']:
        if card not in cards_cache:  # Update cache if needed
            cards_cache[card] = database.get_card(card)
        if cards_cache[card] is None:  # Card missing from database
            tqdm.tqdm.write(f'Missing card from database {card}')
            return False
        if not cards_cache[card]['legal_in_mainboard']:  # Illegal card
            tqdm.tqdm.write(f'Illegal card: {card}')
            return False
        card_color_identity = set(cards_cache[card]['color_identities'])
        if not card_color_identity.issubset(deck_color_identity):
            tqdm.tqdm.write(f"Illegal color identities: {card}, {deck['commanders']}")
            return False

    # If commanders and cards are legal, the deck is legal
    return True


if __name__ == "__main__":
    card_name = "Phyrexian Rager"
    import json
    with open('../server-token.json') as server_token_file:
        test_connection_string = json.load(server_token_file)['connection']
    database = MongoDatabase(test_connection_string)
    from backend.scryfall import get_card_from_scryfall
    card_data = get_card_from_scryfall(card_name, {})
    print(card_data['legal_as_commander'])

    # database.insert_card({'name': card_name, 'needsUpdate': True})
