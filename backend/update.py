"""
Periodically update the deck data.
"""
from typing import Optional
import json
import os
import time
import requests
from backend.database import MongoDatabase
from backend.moxfield import add_moxfield_decks_to_database
from backend.scryfall import get_card_from_scryfall, get_card_names_needing_update
from backend.legality import is_legal


def get_latest_bulk_file(directory: str = "../scryfall_data",
                         delete_older: bool = True) -> Optional[str]:
    """
    Download the latest "oracle-data" cards and then saves them to a file labeled
    "oracle-data-X.json".

    :param directory: Directory to save the oracle data
    :param delete_older: if True, delete older oracle-data files. Default True
    :return: the filepath of the newly downloaded oracle data
    """
    bulk_data_requests = requests.get("https://api.scryfall.com/bulk-data")
    if bulk_data_requests.status_code != requests.codes.ok:
        print("Request failed: Querying bulk data")
        return None
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
        if newest_data_requests.status_code != requests.codes.ok:
            print("Request failed: Downloading bulk data")
            return None
        with open(newest_filepath, "wb") as newest_file:
            newest_file.write(newest_data_requests.content)
        if delete_older:  # Delete older data files
            data_files = os.listdir(f"{directory}")
            for file in data_files:
                if file.startswith('oracle-data') and file != newest_filename:
                    print(f"Deleting {file}")
                    os.remove(f"{directory}/{file}")
        return newest_filepath

    # If file is already downloaded, no update needed
    return newest_filepath


def perform_update(database: MongoDatabase) -> None:
    """
    Insert new decks from Moxfield and new cards into database. Then update
    cards needing updates and check the legality of unconfirmed decks.

    :param database: A Database object containing all card information
    """
    # Step 1: Add decks from Moxfield to the database
    if not add_moxfield_decks_to_database(database):
        print("Error adding decks from Moxfield")
        return

    # Step 2: Update cards that have been added / modified in the latest set
    newest_card = database.cards.find_one(sort=[("updated", -1)])
    if "updated" in newest_card:  # If no cards in database, skip this
        new_cards_to_add = get_card_names_needing_update(newest_card['updated'])
        for card in new_cards_to_add:
            database.insert_card({"name": card, "needsUpdate": True})

    # Step 3: Update cards in need of an update
    # Then have the database update any cards in need of an update:
    scryfall_cache = {}
    # Save all names to close cursor
    cards_needing_update = []
    for card in database.cards.find({"needsUpdate": True}):
        cards_needing_update.append(card['name'])
    for card in cards_needing_update:
        print(f"Updating card {card}")
        start_time = time.time()
        card_data = get_card_from_scryfall(card, scryfall_cache)
        database.insert_card(card_data)
        print(f"Processing time: {time.time() - start_time}")

    # Step 4: Check each deck for illegal cards
    cards_cache = {}
    # Save all decks to close cursor
    decks_needing_check = []
    for deck in database.decks.find({"needsLegalityCheck": True}):
        decks_needing_check.append(deck)
    for deck in decks_needing_check:
        print(deck)
        legal = is_legal(deck, cards_cache, database)
        deck['needsLegalityCheck'] = False
        deck['isLegal'] = legal
        # Always insert so future checks can see if future downshifts make legal
        database.insert_deck(deck)
        if not legal:
            print(f"Illegal deck: https://moxfield.com/decks/{deck['_id']}")


if __name__ == "__main__":
    with open("../server-token.json") as server_token_file:
        connection_string = json.load(server_token_file)['connection']
    test_database = MongoDatabase(connection_string)
