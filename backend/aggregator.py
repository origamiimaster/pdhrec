"""
Reads the data from the database and performs aggregations to calculate
important statistics.
"""
import json
from bson.son import SON
from backend.database import Database


def get_all_scores(database):
    """
    There are 2 main metrics that need to be determined:
    1. Popularity
    2. "Synergy"

    Card popularity is split into two metrics, per commander popularity and
    overall popularity.

    Overall card popularity can be determined by
    CARD_POPULARITY = NUM_DECKS_WITH_CARD / NUM_DECKS

    Per commander card popularity can be determined by counting only decks
    with this card:
    CARD_POPULARITY_WITH_COMMANDER = NUM_DECKS_WITH_COMMANDER_AND_CARD /
        NUM_DECKS_WITH_COMMANDER_TOTAL

    Card synergy requires card popularity with commander, as well as the 
    overall popularity:
    CARD_SYNERGY = CARD_POPULARITY_WITH_COMMANDER - CARD_POPULARITY

    New calculations must also account for only decks that *could* run the
    card, rather than using the total number of decks as the denominator with
    cards that can only be run in a few decks:
    NEW_CARD_POPULARITY = NUM_DECKS_WITH_CARD / NUM_DECKS_WITH_CORRECT_COLOR_IDENTITY
    NEW_CARD_POPULARITY_WITH_COMMANDER = CARD_POPULARITY_WITH_COMMANDER
        = NUM_DECKS_WITH_COMMANDER_AND_CARD / NUM_DECKS_WITH_COMMANDER
    NEW_CARD_SYNERGY = NEW_CARD_POPULARITY_WITH_COMMANDER - NEW_CARD_POPULARITY
    """
    # TODO: Move operations out of memory to take advantage of the database.
    # Initialize statistics to aggregate
    print("Database initialized")
    cards_cached = {}  # Cache card information
    num_color_identity = {}  # Counts of cards by color identity
    commander_color_identities = {}  # Cache of commander color identities
    per_commander_counts = {}  # Counts of decks by commander
    all_cards = {}  # Counts of decks by card
    deck_counts = {}  # Counts of decks by commander then card

    # Initial aggregation of deck counts by color
    for deck in database.decks.aggregate(
            pipeline=[{"$match": {"isLegal": True}},
                      {"$sort": SON([("update_date", -1)])}]):
        # Obtain deck ID and commanders
        deck_id = deck["_id"]
        commanders = tuple(sorted(deck['commanders']))

        # Obtain deck color identity (as commander color identity)
        deck_color_identities = set()
        for commander in commanders:
            # Update with current commander's color identity
            if commander not in cards_cached:  # Load from database then cache
                cards_cached[commander] = database.cards.find_one(
                    {"name": commander})
            if cards_cached[commander] is None:
                print(
                    f"Exception: card not in database: {commander}, {deck_id}")
                exit(1)
            deck_color_identities.update(
                set(cards_cached[commander]['color_identities']))
        deck_color_identities = sorted(list(deck_color_identities))
        deck_color_identities = "".join(deck_color_identities)

        # Record color identity in global statistic
        if deck_color_identities not in num_color_identity:
            num_color_identity[deck_color_identities] = 0
        num_color_identity[deck_color_identities] += 1

        # Cache commander's color identity
        if commanders not in commander_color_identities:
            commander_color_identities[commanders] = deck_color_identities

        # Record commander is in a deck
        if commanders not in per_commander_counts:
            per_commander_counts[commanders] = 0
        per_commander_counts[commanders] += 1

        # Record cards both alongside commander and globally
        if commanders not in deck_counts:
            deck_counts[commanders] = {}
        for card in set(deck['cards']):
            if card not in deck_counts[commanders]:
                deck_counts[commanders][card] = 0
            deck_counts[commanders][card] += 1
            if card not in all_cards:
                all_cards[card] = 0
            all_cards[card] += 1

    # Update user on progress
    print("Done with aggregating initial counts")

    # Calculate per-commander card popularities
    per_commander_popularities = {}
    for commander in deck_counts:
        per_commander_popularities[commander] = {}
        for card in deck_counts[commander]:
            per_commander_popularities[commander][card] = \
                deck_counts[commander][card] / per_commander_counts[commander]
    print("Done normalizing popularities per commander")

    # Calculate overall card popularities
    total_popularities = {}
    color_pipeline = [
        {"$project": {"_id": 0, "name": 1, "color_identities": 1}}]
    card_color_identities = {x['name']: x['color_identities']
                             for x in
                             database.cards.aggregate(pipeline=color_pipeline)}
    for card in all_cards:
        card_color_identity = card_color_identities[card]
        # TODO: Color identity helper function
        allowed_colors = [color_id for color_id in
                          set(commander_color_identities.values())
                          if all([color in color_id for color in
                                  card_color_identity])]
        print(card, allowed_colors)
        # TODO: Precalculate denominators for all color ids
        total_popularities[card] = all_cards[card] / sum(
            [num_color_identity[color_id] for color_id in allowed_colors])
    print("Done normalizing general probabilities")

    # Calculate per-commander synergy scores for cards
    per_commander_synergies = {}
    for commander in per_commander_popularities:
        per_commander_synergies[commander] = {}
        for card in per_commander_popularities[commander]:
            per_commander_synergies[commander][card] = \
            per_commander_popularities[commander][card] - \
            total_popularities[card]

    # Calculate card popularities per color
    per_color_popularities = {}
    # Accumulate total usages of each card. TODO: Why not use all_cards?
    for commanders in deck_counts:
        cards = deck_counts[commanders]
        for card in cards:
            if card not in per_color_popularities:
                per_color_popularities[card] = 0
            per_color_popularities[card] += deck_counts[commanders][card]
    # Calculate decks by color 
    possible_color_identities = list(num_color_identity.keys())
    for card in per_color_popularities:
        card_color_identity = set(card_color_identities[card])
        possible_decks = 0
        for color_id in possible_color_identities:
            if card_color_identity.issubset(set(color_id)):
                possible_decks += num_color_identity[color_id]
        per_color_popularities[card] /= possible_decks  # Normalize
    # Order by decreasing card popularity
    per_color_popularities = dict(sorted(per_color_popularities.items(),
                                         key=lambda item: -item[1]))
    per_color_popularities = {card: (per_color_popularities[card],
                                     card_color_identities[card])
                              for card in per_color_popularities}
    print("Done calculating everything")

    return (per_commander_synergies, per_commander_popularities,
            per_commander_counts, per_color_popularities)


if __name__ == "__main__":
    # Test aggregator function, not storing the produced results
    # Connect to database
    with open("../server-token.json") as f:
        connection_string = json.load(f)['connection']
    print("Building database connection")
    database = Database(connection_string)

    # Calculate statistics
    synergy, popularity, counts, color_popularity = get_all_scores(database)
