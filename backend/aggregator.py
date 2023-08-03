"""
Reads the data from the database and performs aggregations to calculate
important statistics.
"""
import json
from bson.son import SON
from backend.database import Database
from backend.utils import color_identities


def get_all_scores(database: Database) -> tuple[dict, dict, dict, dict]:
    """
    There are 2 main metrics that need to be determined:
    1. Popularity
    2. "Synergy"

    Card usage is split into two metrics, per commander usage and
    overall usage.

    Overall card popularity can be determined by
    CARD_USAGE = NUM_DECKS_WITH_CARD / NUM_DECKS_CAN_RUN_CARD

    Per commander card usage can be determined by counting only decks
    with this card:
    CARD_USAGE_WITH_COMMANDER = NUM_DECKS_WITH_COMMANDER_AND_CARD /
        NUM_DECKS_WITH_COMMANDER

    Card synergy measures a commander's preference for a card through
    card usage with commander and overall usage:
    CARD_SYNERGY = CARD_POPULARITY_WITH_COMMANDER - CARD_POPULARITY
    """
    # Query database for all relevant card counts and color identities
    (color_identity_counts, commander_counts, card_counts,
     commander_card_counts) = aggregate_counts(database)
    card_color_identities = get_card_color_identities(database)

    # Calculate needed statistics from the queried data
    per_commander_use = calculate_card_use_per_commander(commander_card_counts,
                                                         commander_counts)
    card_use = calculate_card_use(card_counts, card_color_identities,
                                  color_identity_counts)
    per_commander_synergy = calculate_card_synergy(per_commander_use, card_use)
    sorted_card_use = sort_cards_by_use(card_use, card_color_identities)

    return (per_commander_synergy, per_commander_use,
            commander_counts, sorted_card_use)


def aggregate_counts(database: Database) -> tuple[dict, dict, dict, dict]:
    """
    Query the database for deck information and aggregate the decklists into
    deck counts by color identity, how deck counts by commander,
    deck counts by card, and deck counts by commander by card.
    """
    # TODO: Move operations out of memory to take advantage of the database.
    # Initialize statistics to aggregate
    print("Database initialized")
    # Create card and color identity caches
    cards_cached = {}  # Cache card information
    commander_color_identities = {}  # Cache of commander color identities

    # Create dictionaries to record counts of card usage
    color_identity_counts = {}  # {Color identity: Count of decks}
    commander_counts = {}  # {Commander: Count of decks}
    card_counts = {}  # {Card: Count of decks}
    commander_card_counts = {}  # Commander: {Card: Count of Decks}

    # Initial aggregation of deck counts by color
    aggregate_pipeline = [{"$match": {"isLegal": True}},
                          {"$sort": SON([("update_date", -1)])}]
    for deck in database.decks.aggregate(pipeline=aggregate_pipeline):
        # Obtain deck ID and commanders
        deck_id = deck["_id"]
        commanders = tuple(sorted(deck['commanders']))

        # Obtain deck color identity (as commanders' color identity)
        if commanders not in commander_color_identities:
            deck_color_identities = set()
            for commander in commanders:
                # Update with current commander's color identity
                if commander not in cards_cached:  # Load from database then cache
                    cards_cached[commander] = database.cards.find_one({"name": commander})
                if cards_cached[commander] is None:
                    print(f"Exception: card not in database: {commander}, {deck_id}")
                    exit(1)
                commander_color_identity = set(cards_cached[commander]['color_identities'])
                deck_color_identities.update(commander_color_identity)
            deck_color_identities = sorted(list(deck_color_identities))
            deck_color_identities = "".join(deck_color_identities)
            commander_color_identities[commanders] = deck_color_identities
        else:
            deck_color_identities = commander_color_identities[commanders]

        # Increment count of color identity
        if deck_color_identities not in color_identity_counts:
            color_identity_counts[deck_color_identities] = 0
        color_identity_counts[deck_color_identities] += 1

        # Record commander is in a deck
        if commanders not in commander_counts:
            commander_counts[commanders] = 0
        commander_counts[commanders] += 1

        # Record cards both alongside commander and globally
        if commanders not in commander_card_counts:
            commander_card_counts[commanders] = {}
        for card in set(deck['cards']):
            if card not in commander_card_counts[commanders]:
                commander_card_counts[commanders][card] = 0
            commander_card_counts[commanders][card] += 1
            if card not in card_counts:
                card_counts[card] = 0
            card_counts[card] += 1

    # Update user on progress
    print("Aggregated count data")
    return (color_identity_counts, commander_counts, card_counts,
            commander_card_counts)


def calculate_card_use_per_commander(commander_card_counts: dict,
                                     commander_counts: dict) -> dict:
    """
    NEW_CARD_POPULARITY_WITH_COMMANDER = CARD_POPULARITY_WITH_COMMANDER
        = NUM_DECKS_WITH_COMMANDER_AND_CARD / NUM_DECKS_WITH_COMMANDER
    """
    # For each commander, calculate popularity of each card played with it
    card_use_per_commander = {}
    for commander in commander_card_counts:
        card_use_per_commander[commander] = {}
        for card in commander_card_counts[commander]:
            card_use_per_commander[commander][card] = \
                commander_card_counts[commander][card] / commander_counts[commander]

    print("Calculated card per commander use frequencies")
    return card_use_per_commander


def get_card_color_identities(database: Database) -> dict:
    """
    Query the database on the color identity of all cards.
    Return as dictionary of card: color identity.
    """
    # Cache card color identities
    color_pipeline = [{"$project": {"_id": 0, "name": 1, "color_identities": 1}}]
    return {card['name']: card['color_identities']
            for card in database.cards.aggregate(pipeline=color_pipeline)}


def calculate_card_use(card_counts: dict, card_color_identities: dict,
                       color_identity_counts: dict) -> dict:
    """
    NEW_CARD_POPULARITY = NUM_DECKS_WITH_CARD / NUM_DECKS_WITH_CORRECT_COLOR_IDENTITY
    """
    # Calculate total number of decks which can run a card of a given
    # color identity
    color_superset_counts = \
        calculate_color_superset_counts(color_identity_counts)

    # Calculate overall card usage rate in decks able to run card
    card_use = {}
    for card in card_counts:
        card_color_identity = card_color_identities[card]
        card_use[card] = (card_counts[card] /
                          color_superset_counts[card_color_identity])

    print("Calculated card general use frequencies")
    return card_use


def calculate_color_superset_counts(color_identity_counts: dict) -> dict:
    """
    For each color identity, determine the number of decks able to run cards
    of that color identity.
    A deck with a color identity which is a superset of a card's color
    identity can run that card.
    """
    color_superset_counts = {}
    for key_color_id in color_identities:
        color_superset_counts[key_color_id] = 0
        for deck_color_id in color_identity_counts:
            if set(key_color_id).issubset(deck_color_id):
                color_superset_counts[key_color_id] += \
                    color_identity_counts[deck_color_id]
    return color_superset_counts


def calculate_card_synergy(per_commander_use: dict, card_use: dict) -> dict:
    """
    NEW_CARD_SYNERGY = NEW_CARD_POPULARITY_WITH_COMMANDER - NEW_CARD_POPULARITY
    """
    per_commander_synergy = {}
    for commander in per_commander_use:
        per_commander_synergy[commander] = {}
        for card in per_commander_use[commander]:
            per_commander_synergy[commander][card] = \
                (per_commander_use[commander][card] - card_use[card])
    return per_commander_synergy


def sort_cards_by_use(card_use: dict, card_color_identities: dict) -> dict:
    """
    Sort the use rate of cards in decreasing order, to create the staples page.
    Include color identity in the value for easier sorting.
    """
    sorted_card_use = dict(sorted(card_use.items(),
                                  key=lambda item: -item[1]))
    return {card: (sorted_card_use[card], card_color_identities[card])
            for card in sorted_card_use}


if __name__ == "__main__":
    # Test aggregator function, not storing the produced results
    # Connect to database
    with open("../server-token.json") as f:
        connection_string = json.load(f)['connection']
    print("Building database connection")
    database = Database(connection_string)

    # Calculate statistics
    synergy, popularity, counts, color_popularity = get_all_scores(database)
