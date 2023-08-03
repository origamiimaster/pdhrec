"""
Periodically update the deck data.
"""
import json
import os
import time
import requests
from dateutil import parser

from backend.database import MongoDatabase
from backend.moxfield import convert_to_deck, get_deck_data, get_new_decks
from backend.scryfall import get_card_object, get_card_names_for_cards_needing_updates
from backend.legality import check_legality


def get_latest_bulk_file(directory="../scryfall_data",
                         delete_older=True) -> str:
    """
    Gets the latest "oracle-data" cards and then saves them to a file labeled
    "oracle-data-X.json".
    """
    bulk_data_requests = requests.get("https://api.scryfall.com/bulk-data")
    bulk_data_json = bulk_data_requests.json()
    newest_version = [card_data for card_data in bulk_data_json['data']
                      if card_data['type'] == "oracle_cards"][0]
    newest_filename = newest_version['download_uri'].split('/')[-1]
    newest_filepath = f"{directory}/{newest_filename}"
    print("Checking bulk file version")
    # If the latest data is not downloaded, save it
    if not os.path.isfile(newest_filepath):
        print("New bulk file found")
        newest_data_requests = requests.get(newest_version["download_uri"])
        with open(newest_filepath, "wb") as newest_file:
            newest_file.write(newest_data_requests.content)

        if delete_older:  # Delete older data files
            data_files = os.listdir(f"{directory}")
            for file in data_files:
                if file == newest_filename or file == ".gitignore":
                    pass
                else:
                    print(f"Deleting {file}")
                    os.remove(f"{directory}/{file}")

        # TODO: Should this be re-implemented? If not, delete
        # Since we've got a new file, some cards can have changed rarities.  Switch over the "needs legality check"
        # flag.
        # database.cards.update_many({}, {"$set": {"needsUpdate": True}})
        # database.decks.update_many({}, {"$set": {"needsLegalityCheck": True}})
        return newest_filepath

    # If file is already downloaded, no update needed
    return newest_filepath


def perform_update(database):
    print("Auto updating decks to database")

    # Step 1: Update decks. Find the most recently updated deck in the
    # database, then iterate over the full decklist backwards in time until
    # that most recent deck is found forwards in time updating all decks more
    # recent than that.
    latest_updated_deck = database.decks.find_one(sort=[("update_date", -1)])
    if latest_updated_deck is None:  # If database starts empty
        latest_updated_time = 1690828409.017133
    else:
        latest_updated_time = latest_updated_deck['update_date']
    new_decks = get_new_decks(1)  # Page 1 of all decks
    newest_deck = new_decks[0]
    newest_time = parser.parse(newest_deck['lastUpdatedAtUtc']).timestamp()

    print("Updating")
    curr_deck_time = newest_time
    curr_page = 1  # Results are paginated
    # Update decks in reverse chronological order until last updated deck
    while latest_updated_time < curr_deck_time:
        for deck in new_decks:
            if latest_updated_time >= curr_deck_time:
                break

            print(f"Saving deck {deck['name']}")
            # Save the new deck to the database
            queried_deck_data = get_deck_data(deck['publicId'])
            if not queried_deck_data:
                continue
            deck_obj = convert_to_deck(queried_deck_data).to_dict()
            deck_obj['needsLegalityCheck'] = True
            database.insert_deck(deck_obj)

            # Update curr_deck_time and break if older than
            curr_deck_time = deck_obj['update_date']
        # Wait for 1 second to respect APIs
        time.sleep(1)
        # Page fully processed so progress to next page
        curr_page += 1
        new_decks = get_new_decks(curr_page)

    # Step 1.5: Update cards that have been added / modified in the latest set:
    newest_card = database.cards.find_one(sort=[("updated", -1)])
    if "updated" in newest_card:
        new_cards_to_add = get_card_names_for_cards_needing_updates(
            newest_card['updated'])
        for card in new_cards_to_add:
            database.insert_card({"name": card, "needsUpdate": True})

    # Step 2: Update cards in need of an update
    # Then have the database update any cards in need of an update:
    # cursor = database.cards.find({"needsUpdate": True})
    # entries_in_mem = [x for x in cursor]
    # entries_in_mem = database.cards.find({})
    cards_needing_update = [x for x in database.cards.find({"needsUpdate": True})]
    for card in cards_needing_update:
        print(f"Updating card {card['name']}")
        start_time = time.time()
        card_data = get_card_object(card['name'])
        if card_data is False:  # No data for card
            card_data = card
            card_data['needsUpdate'] = False
            card_data['legal_in_mainboard'] = False
            card_data['legal_as_commander'] = False
            card_data['error'] = True
        else:
            card_data = card_data.to_dict()

        database.insert_card(card_data)
        print(time.time() - start_time)

    # Step 3:
    # Check each deck for illegal cards
    # database.decks.update_many({}, {"$set": {"needsLegalityCheck": True}})
    cards_cache = {}
    for deck in database.decks.find({"needsLegalityCheck": True}):
        print(deck)
        legal = check_legality(deck, cards_cache, database)
        deck['needsLegalityCheck'] = False
        # TODO: Should the database contain illegal decks?
        deck['isLegal'] = legal
        database.insert_deck(deck)
        if not legal:
            print(f"Illegal deck: https://moxfield.com/decks/{deck['_id']}")


if __name__ == "__main__":
    with open("../server-token.json") as server_token_file:
        connection_string = json.load(server_token_file)['connection']
    database = MongoDatabase(connection_string)
    # Begin an auto update?
    # get_latest_bulk_file(database)
    # perform_update(database)
