"""
Gets the data from the database, and does some aggregations to determine the different values.
"""
import json
from bson.son import SON

from backend.database import Database

"""
We have a couple of considerations to keep in mind: 
1. For each card, we need to get a list of how many decks exist with it, and a list of how many decks could have it 
but do not.  
a. Iterate through decks, increment card sum dictionary or something each time we spot it.  
b. Sort decks by timestamp? Then start at the point where the card already exists, count forward.  

2. We only care about color identity.  Sort decks into different lists based on color identity? 


Any way I do this, it seems like there will be a bunch of work with iterating through C cards and D decks, nested...
"""
with open("../server-token.json") as f:
    connection_string = json.load(f)['connection']
print("Building database connection")
database = Database(connection_string)

# For now, performing all operations in memory.  Later, will rewrite to take advantage of the database.
print("Database initialized")

cards_cached = {}

num_color_identity = {}
color_identity_counts = {}

commander_color_identities = {}

num_decks = {}
deck_counts = {}
for deck in database.decks.aggregate(pipeline=[{"$match": {"isLegal": True}},
                                               {"$sort": SON([("update_date", -1)])}]):
    deck_id = deck["_id"]
    commanders = tuple(deck['commanders'])
    print(deck_id)

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
    if color_identities not in color_identity_counts:
        color_identity_counts[color_identities] = 0
    color_identity_counts[color_identities] += 1

    if commanders not in commander_color_identities:
        commander_color_identities[commanders] = color_identities



    if commanders not in num_decks:
        num_decks[commanders] = 0
    num_decks[commanders] += 1

    if commanders not in deck_counts:
        deck_counts[commanders] = {}
    for card in deck['cards']:
        if card not in deck_counts[commanders]:
            deck_counts[commanders][card] = 0
        deck_counts[commanders][card] += 1


print("Done with aggregating initial things")

# For every deck, we have a count
#
# counts_decks_with_cards = {}
# for card in database.cards_cache:
#     print(card)

# cards = database.cards.find({})
# decks = [d for d in database.decks.find({})]

list_of_deck_ids = []

# for deck in database.decks.find({}, sort=[("update_date", -1)]):
#     print(deck)
# values =
# card_dates_in_order = [x for x in database.cards.aggregate(pipeline=[{"$sort": SON([("released", -1)])},
#                                                                      {"$project": {"_id": 0, "released": 1,
#                                                                                    "name": 1}}])]

# for deck in database.decks.aggregate(pipeline=[{"$sort": SON([("update_date", -1)])},
#                                                {"$project": {"_id": 1, "update_date": 1}}]):
#     print(deck)




# print("Sorting")
# sorted_decks = sorted(decks, key=lambda x: x['update_date'])
# print("Successfully sorted")


