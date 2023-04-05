"""
Gets the data from the database, and does some aggregations to determine the different values.
"""
import json
from bson.son import SON

from backend.database import Database


def get_all_scores(database):
    """
    There are 2 main metrics that need to be determined:
    1. Popularity
    2. "Synergy"

    Card popularity is split into two metrics, per commander popularity and overall popularity.

    Overall card popularity can be determined by
    CARD_POPULARITY = NUM_DECKS_WITH_CARD / NUM_DECKS

    Per commander card popularity can be determined by counting only decks with this card:
    CARD_POPULARITY_WITH_COMMANDER = NUM_DECKS_WITH_COMMANDER_AND_CARD / NUM_DECKS_WITH_COMMANDER_TOTAL

    Card synergy requires card popularity with commander, as well as the overall popularity.
    CARD_SYNERGY = CARD_POPULARITY_WITH_COMMANDER - CARD_POPULARITY

    New calculations must also account for all decks that *could* run the card, and not include denominators with cards
    that can only be run in a few decks.

    NEW_CARD_POPULARITY = NUM_DECKS_WITH_CARD / NUM_DECKS_WITH_CORRECT_COLOR_IDENTITY

    NEW_CARD_POPULARITY_WITH_COMMANDER = CARD_POPULARITY_WITH_COMMANDER
    = NUM_DECKS_WITH_COMMANDER_AND_CARD / NUM_DECKS_WITH_COMMANDER

    NEW_CARD_SYNERGY = NEW_CARD_POPULARITY_WITH_COMMANDER - NEW_CARD_POPULARITY
    """
    # For now, performing all operations in memory.  Later, will rewrite to take advantage of the database.
    print("Database initialized")

    cards_cached = {}

    num_color_identity = {}
    color_identity_counts = {}

    commander_color_identities = {}

    num_decks = {}

    all_cards = {}

    deck_counts = {}
    for deck in database.decks.aggregate(pipeline=[{"$match": {"isLegal": True}},
                                                   {"$sort": SON([("update_date", -1)])}]):
        deck_id = deck["_id"]
        commanders = tuple(sorted(deck['commanders']))

        color_identities = set()
        for commander in commanders:
            if commander not in cards_cached:
                cards_cached[commander] = database.cards.find_one({"name": commander})
            if cards_cached[commander] is None:
                print(f"Exception: card not in database: {commander}, {deck_id}")
                exit(1)
            color_identities.update(set(cards_cached[commander]['color_identities']))
        color_identities = list(color_identities)
        color_identities.sort()
        color_identities = "".join(color_identities)
        if color_identities not in num_color_identity:
            num_color_identity[color_identities] = 0
        num_color_identity[color_identities] += 1

        if commanders not in commander_color_identities:
            commander_color_identities[commanders] = color_identities

        if commanders not in num_decks:
            num_decks[commanders] = 0
        num_decks[commanders] += 1

        if commanders not in deck_counts:
            deck_counts[commanders] = {}
        for card in set(deck['cards']):
            if card not in deck_counts[commanders]:
                deck_counts[commanders][card] = 0
            deck_counts[commanders][card] += 1
            if card not in all_cards:
                all_cards[card] = 0
            all_cards[card] += 1

    print("Done with aggregating initial things")

    per_commander_popularities = {}
    for commander in deck_counts:
        per_commander_popularities[commander] = {}
        for card in deck_counts[commander]:
            per_commander_popularities[commander][card] = deck_counts[commander][card] / num_decks[commander]

    print("Done normalizing popularities per commander")

    total_commander_popularities = {}

    color_identities = {x['name']: x['color_identities'] for x in
                        database.cards.aggregate(pipeline=[{"$project": {"_id": 0, "name": 1, "color_identities": 1}}])}
    for card in all_cards:
        color_identity = color_identities[card]
        allowed_colors = [x for x in set(commander_color_identities.values()) if all([y in x for y in color_identity])]
        total_commander_popularities[card] = all_cards[card] / sum([num_color_identity[x] for x in allowed_colors])

    print("Done normalizing general probabilities")

    per_commander_synergies = {}

    for commander in per_commander_popularities:
        per_commander_synergies[commander] = {}
        for card in per_commander_popularities[commander]:
            per_commander_synergies[commander][card] = per_commander_popularities[commander][card] - \
                                                       total_commander_popularities[card]

    per_commander_counts = num_decks

    per_color_popularities = {}
    for commanders in deck_counts:
        cards = deck_counts[commanders]
        for card in cards:
            if card not in per_color_popularities:
                per_color_popularities[card] = 0
            per_color_popularities[card] += deck_counts[commanders][card]
    possible_color_identities = list(num_color_identity.keys())
    for card in per_color_popularities:
        card_color_identity = set(color_identities[card])
        total_count = 0
        for thing in possible_color_identities:
            if card_color_identity.issubset(set(thing)):
                total_count += num_color_identity[thing]
        per_color_popularities[card] /= total_count
    per_color_popularities = dict(sorted(per_color_popularities.items(), key=lambda item: -item[1]))
    per_color_popularities = {x: (per_color_popularities[x], color_identities[x]) for x in per_color_popularities}
    print("Done calculating everything")

    return (per_commander_synergies, per_commander_popularities, per_commander_counts, per_color_popularities)


if __name__ == "__main__":
    with open("../server-token.json") as f:
        connection_string = json.load(f)['connection']
    print("Building database connection")
    database = Database(connection_string)
    synergy, popularity, counts, color_popularity = get_all_scores(database)
