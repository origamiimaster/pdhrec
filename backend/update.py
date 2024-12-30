"""
Periodically update the deck data.
"""
from typing import Optional
import json
import os
import time
import requests
import re
from backend.database import MongoDatabase
from backend.decksource import _DeckSource
from backend.moxfield import MoxfieldDeckSource
from backend.scryfall import get_card_from_scryfall, \
    get_card_names_needing_update
from backend.legality import is_legal
import tqdm


def get_latest_bulk_file(directory: str = '../scryfall_data',
                         delete_older: bool = True) -> Optional[str]:
    """
    Download the latest "oracle-data" cards and then saves them to a file labeled
    "oracle-data-X.json".

    :param directory: Directory to save the oracle data
    :param delete_older: if True, delete older oracle-data files. Default True
    :return: the filepath of the newly downloaded oracle data
    """
    bulk_data_requests = requests.get('https://api.scryfall.com/bulk-data')
    if bulk_data_requests.status_code != requests.codes.ok:
        print('Request failed: Querying bulk data')
        return None
    bulk_data_json = bulk_data_requests.json()
    newest_version = [card_data for card_data in bulk_data_json['data']
                      if card_data['type'] == 'oracle_cards'][0]
    newest_filename = newest_version['download_uri'].split('/')[-1]
    newest_filepath = f'{directory}/{newest_filename}'
    print('Checking bulk file version')
    # If the latest data is not downloaded, save it
    if not os.path.isfile(newest_filepath):
        print('New bulk file found')
        newest_data_requests = requests.get(newest_version['download_uri'])
        if newest_data_requests.status_code != requests.codes.ok:
            print('Request failed: Downloading bulk data')
            return None
        with open(newest_filepath, 'wb') as newest_file:
            newest_file.write(newest_data_requests.content)
        if delete_older:  # Delete older data files
            data_files = os.listdir(f'{directory}')
            for file in data_files:
                if file.startswith('oracle-data') and file != newest_filename:
                    print(f'Deleting {file}')
                    os.remove(f'{directory}/{file}')
        return newest_filepath

    # If file is already downloaded, no update needed
    return newest_filepath


def perform_update(database: MongoDatabase, deck_sources: list[_DeckSource]) -> \
        None:
    """
    Insert new decks from Moxfield and new cards into database. Then update
    cards needing updates and check the legality of unconfirmed decks.

    :param deck_sources: A list of DeckSources to load decks from.
    :param database: A Database object containing all card information
    """
    # Step 1: Add new decks from all sources to the database
    for source in deck_sources:
        if not add_source_to_database(source, database):
            print(f"Error adding decks from {source.__class__.__name__}")
    # Step 2: Update cards that have been added / modified in the latest set
    newest_card = database.cards.find_one({"$or": [
        {"legal_as_commmander": True}, {"legal_in_mainboard": True}]
    },
        sort=[('released', -1)])
    if 'released' in newest_card:  # If no cards in database, skip this
        new_cards_to_add = get_card_names_needing_update(
            newest_card['released'])
        for card in tqdm.tqdm(new_cards_to_add):
            # database.insert_card({'name': card, 'needsUpdate': True})
            database.update_card({'name': card, 'needsUpdate': True})

    # Step 3: Update cards in need of an update
    # Then have the database update any cards in need of an update:
    scryfall_cache = {}
    # Save all names to close cursor
    cards_needing_update = []
    for card in tqdm.tqdm(database.cards.find({'needsUpdate': True})):
        cards_needing_update.append(card['name'])
    for card in tqdm.tqdm(cards_needing_update):
        tqdm.tqdm.write(f'Updating card {card}')
        start_time = time.time()
        card_data = get_card_from_scryfall(card, scryfall_cache)
        # database.insert_card(card_data)
        database.update_card(card_data)
        tqdm.tqdm.write(f'Processing time: {time.time() - start_time}')

    # Step 4: Check each deck for illegal cards
    cards_cache = {}
    # Save all decks to close cursor
    decks_needing_check = []
    for deck in database.decks.find({'needsLegalityCheck': True}):
        decks_needing_check.append(deck)

    for deck in tqdm.tqdm(decks_needing_check):
        # print(deck)
        legal = is_legal(deck, cards_cache, database)
        deck['needsLegalityCheck'] = False
        deck['isLegal'] = legal
        # Always insert so future checks can see if future downshifts make legal
        database.insert_deck(deck)
        if not legal:
            if deck['source'] == "moxfield":
                tqdm.tqdm.write(
                    f"Illegal deck: https://moxfield.com/decks/{deck['_id'][9:]}")
            elif deck['source'] == 'archidekt':
                tqdm.tqdm.write(
                    f"Illegal deck: https://archidekt.com/decks/{deck['_id'][10:]}")
            else:
                tqdm.tqdm.write(f"Illegal deck from unknown source. ID ="
                                f" {deck['_id']}")


def add_source_to_database(source: _DeckSource, database) -> bool:
    """
    Gets new decks from the source and inserts them into the database,
    only newer decks than the most recently updated database deck.

    :param source: A _DeckSource object to collect decks from.
    :param database: A Database object to insert decks into.
    :return: True if all decks updated, False if an error occurred.
    """
    tqdm.tqdm.write(f"Inserting decks from {source.__class__.__name__} into"
          f" {database.__class__.__name__}")
    latest_updated_deck = database.decks.find_one(
        {'source': source.name}, sort=[('update_date', -1)]
    )
    # If the database starts empty, we pick an arbitrary amount of time.
    if latest_updated_deck is None:
        latest_updated_time = None
    else:
        latest_updated_time = latest_updated_deck['update_date']

    try:
        decks_to_update = source.get_new_decks(latest_updated_time)

        for deck in tqdm.tqdm(decks_to_update):
            tqdm.tqdm.write(f"Inserting {deck['_id']}")
            deck['needsLegalityCheck'] = True
            database.insert_deck(deck)
        return True
    except ValueError:
        return False


if __name__ == '__main__':
    with open('../server-token.json') as server_token_file:
        connection_string = json.load(server_token_file)['connection']
    test_database = MongoDatabase(connection_string)
    test_source = MoxfieldDeckSource()
    perform_update(test_database, [test_source])
