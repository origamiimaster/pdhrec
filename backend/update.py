"""
Periodically update the deck data.
"""
from typing import Optional
import json
import os
import time
import requests
from pathlib import Path
import re
from backend.database import MongoDatabase
from backend.decksource import _DeckSource
from backend.moxfield import MoxfieldDeckSource
from backend.archidekt import ArchidektDeckSource
from backend.scryfall import get_card_from_scryfall, \
    get_card_names_needing_update, build_scryfall_index
from backend.legality import is_legal
import tqdm


def get_latest_bulk_file(directory: str = '../scryfall_data',
                         delete_older: bool = True) -> str:
    """
    Download the latest "oracle-data" cards and then saves them to a file labeled
    "oracle-data-X.json".

    :param directory: Directory to save the oracle data
    :param delete_older: if True, delete older oracle-data files. Default True
    :return: the filepath of the newly downloaded oracle data
    """
    bulk_data_requests = requests.get('https://api.scryfall.com/bulk-data', headers={
        "User-Agent": "PDHREC/1.0",
        "Accept": "*/*"
    }
    )

    BASE_DIR = Path(__file__).resolve().parent
    directory = os.path.join(BASE_DIR, directory)

    if bulk_data_requests.status_code != requests.codes.ok:
        print('Request failed: Querying bulk data')
        return None
    bulk_data_json = bulk_data_requests.json()
    newest_version = [card_data for card_data in bulk_data_json['data']
                      if card_data['type'] == 'oracle_cards'][0]
    newest_filename = newest_version['jsonl_download_uri'].split('/')[-1]
    newest_filepath = f'{directory}/{newest_filename}'
    print('Checking bulk file version')
    # If the latest data is not downloaded, save it
    if not os.path.isfile(newest_filepath):
        print('New bulk file found')
        newest_data_requests = requests.get(newest_version['jsonl_download_uri'], headers={
            "User-Agent": "PDHREC/1.0",
            "Accept": "*/*"
        })
        if newest_data_requests.status_code != requests.codes.ok:
            print('Request failed: Downloading bulk data')
            raise ValueError('Request failed: Downloading bulk data')
        with open(newest_filepath, 'wb') as newest_file:
            newest_file.write(newest_data_requests.content)
        if delete_older:  # Delete older data files
            data_files = os.listdir(f'{directory}')
            for file in data_files:
                if file.startswith('oracle-cards') and file != newest_filename:
                    print(f'Deleting {file}')
                    os.remove(os.path.join(directory, file))
        return newest_filepath

    # If file is already downloaded, no update needed
    return newest_filepath


def get_latest_full_bulk_file(directory: str = '../scryfall_data',
                              delete_older: bool = True) -> str:
    """
    Download the latest "full" (default_cards) bulk data and save it to a
    file labeled "default-cards-X.json".

    default_cards contains every printing of every card (one language per
    card), unlike oracle_cards which collapses each card down to a single
    printing. This is the file backend.scryfall.build_scryfall_index expects,
    since choose_image needs multiple printings per card to pick the best
    image from.

    This function is independent of get_latest_bulk_file (oracle_cards) --
    it downloads to the same directory but tracks its own "default-cards"
    filename prefix for version checking / cleanup, so it does not interact
    with or affect the oracle data file in any way.

    :param directory: Directory to save the full bulk data
    :param delete_older: if True, delete older default-cards files. Default True
    :return: the filepath of the newly downloaded full bulk data
    """
    bulk_data_requests = requests.get('https://api.scryfall.com/bulk-data', headers={
        "User-Agent": "PDHREC/1.0",
        "Accept": "*/*"
    }
    )
    BASE_DIR = Path(__file__).resolve().parent
    directory = os.path.join(BASE_DIR, directory)

    if bulk_data_requests.status_code != requests.codes.ok:
        print('Request failed: Querying bulk data')
        return None
    bulk_data_json = bulk_data_requests.json()
    newest_version = [card_data for card_data in bulk_data_json['data']
                      if card_data['type'] == 'default_cards'][0]
    newest_filename = newest_version['jsonl_download_uri'].split('/')[-1]
    newest_filepath = f'{directory}/{newest_filename}'
    print('Checking full bulk file version')
    # If the latest data is not downloaded, save it
    if not os.path.isfile(newest_filepath):
        print('New full bulk file found')
        newest_data_requests = requests.get(newest_version['jsonl_download_uri'], headers={
            "User-Agent": "PDHREC/1.0",
            "Accept": "*/*"
        })
        if newest_data_requests.status_code != requests.codes.ok:
            print('Request failed: Downloading full bulk data')
            raise ValueError('Request failed: Downloading full bulk data')
        with open(newest_filepath, 'wb') as newest_file:
            newest_file.write(newest_data_requests.content)
        if delete_older:  # Delete older data files
            data_files = os.listdir(f'{directory}')
            for file in data_files:
                if file.startswith('default-cards') and file != newest_filename:
                    print(f'Deleting {file}')
                    os.remove(os.path.join(directory, file))
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

    # Download bulk data. The oracle_cards file is downloaded here to
    # preserve existing behavior for anything else in the codebase that
    # depends on get_latest_bulk_file; its return value is otherwise unused
    # in this function. The default_cards ("full") file is used to build
    # the card_index used for card lookups below.
    oracle_bulk_filepath = get_latest_bulk_file()
    full_bulk_filepath = get_latest_full_bulk_file()
    card_index = build_scryfall_index(full_bulk_filepath) if full_bulk_filepath else {}

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
        # start_time = time.time()
        card_data = get_card_from_scryfall(card, card_index, scryfall_cache)
        # database.insert_card(card_data)
        database.update_card(card_data)
        # tqdm.tqdm.write(f'Processing time: {time.time() - start_time}')

    # Step 4: Check each deck for illegal cards
    cards_cache = {}
    # Save all decks to close cursor
    decks_needing_check = []
    for deck in database.decks.find({'needsLegalityCheck': True}):
        decks_needing_check.append(deck)

    all_card_names = set()
    for deck in database.decks.find({'needsLegalityCheck': True}):
        all_card_names.update(deck['commanders'])
        all_card_names.update(deck['cards'])

    for card_doc in database.cards.find({'name': {'$in': list(all_card_names)}}):
        cards_cache[card_doc['name']] = card_doc

    for deck in tqdm.tqdm(decks_needing_check):
        # print(deck)
        legal = is_legal(deck, cards_cache, database)
        deck['needsLegalityCheck'] = False
        deck['isLegal'] = legal
        # Always insert so future checks can see if future downshifts make legal
        database.insert_deck(deck, cards_cache)
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
    test_source = ArchidektDeckSource()
    perform_update(test_database, [test_source])
