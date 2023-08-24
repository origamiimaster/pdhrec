"""
Generates files to build the frontend.
"""

import json
from backend.aggregator import get_all_scores, get_card_color_identities
from backend.database import MongoDatabase
from backend.moxfield import MoxfieldDeckSource
from backend.archidekt import ArchidektDeckSource
from backend.utils import normalize_cardnames
from backend.update import perform_update, get_latest_bulk_file

if __name__ == '__main__':
    # Create a connection to the database
    with open('server-token.json') as server_token_file:
        connection_string = json.load(server_token_file)['connection']
    database = MongoDatabase(connection_string)
    sources = [ArchidektDeckSource(), MoxfieldDeckSource()]

    # Commit updates to the database
    print('Updating database')
    perform_update(database, sources)

    # Load all cards from bulk json in database
    bulk_filepath = get_latest_bulk_file(directory='scryfall_data')
    with open(bulk_filepath, 'r') as bulk_file:
        all_card_data = json.load(bulk_file)

    # Create lookup of card images by name, alongside sets of lands and DFCs
    image_lookup = {}
    image_pipeline = [{'$match': {'$or': [{'legal_in_mainboard': True},
                                          {'legal_as_commander': True}]}},
                      {'$project': {'_id': 0, 'image_urls': 1, 'name': 1}}]
    for card in database.cards.aggregate(image_pipeline):
        image_lookup[card['name']] = card['image_urls']
    lands = set()
    double_faced = set()
    for card in all_card_data:
        if 'type_line' not in card:
            continue
        if 'Land' in card['type_line']:
            lands.add(card['name'])
        # Skip tokens
        if 'set_type' in card and card['set_type'] == 'token':
            continue
        # Double-faced cards
        if 'image_uris' not in card and 'card_faces' in card:
            double_faced.add(card['name'])

    # Generate a list of the commanders / commander pairs, along with their 
    # image urls and cleaned names
    commander_pipeline = [{'$match': {'isLegal': True}},
                          {'$project': {'_id': 0, 'commanders': 1}}]
    commanders_list = {tuple(deck['commanders'])
                       for deck in database.decks.aggregate(commander_pipeline)}
    # Ensure commanders are unique (sort pairs)
    commanders_list = list(set(tuple(sorted(commanders))
                               for commanders in commanders_list))

    # Store all updated commander data
    commander_data = []
    # Record commander names and image URLs
    for commanders in commanders_list:
        urls = []
        for card in commanders:
            urls.extend(database.cards.find_one({'name': card})['image_urls'])
        commander_data.append({'commanders': commanders, 'urls': urls})

    # Record all other commander statistics
    all_synergy_scores, popularity_scores, commander_counts, \
        color_popularity, commander_card_counts = get_all_scores(database)

    # Get color identities for commander filtering by color
    card_color_identities = get_card_color_identities(database)

    processed = 0  # Number of commanders processed
    commander_names = []
    for commander in commander_data:
        print(f'Updating: {commander}')
        # Store commander name
        commander_names.append(" ".join(commander['commanders']))
        # Store count of decks with commander
        commander['count'] = commander_counts[tuple(commander['commanders'])]

        # Store synergy scores
        commander['carddata'] = []
        synergy_scores = all_synergy_scores[tuple(commander['commanders'])]
        for card in synergy_scores:
            if card in image_lookup:
                card_image = image_lookup[card]
            else:
                raise Exception(f'{card} not in image_lookup')
            card_popularity = commander_card_counts[tuple(commander[
                                                              'commanders'])][card]
            card_info = [card, synergy_scores[card], card_image, card_popularity]
            commander['carddata'].append(card_info)
        # Sort cards by decreasing synergy scores
        commander['carddata'].sort(key=lambda info: -info[1])

        if len(commander['commanders']) == 1:
            commander['coloridentity'] = card_color_identities[commander[
                'commanders'][0]]
        else:
            commander['coloridentity'] = "".join(sorted(set(
                card_color_identities[commander['commanders'][0]] +
                card_color_identities[commander['commanders'][1]])))

        # Parse commanders and commanderstring (for database use)
        # Double faced commanders separated by '--'
        if (len(commander['commanders']) == 1
                and commander['commanders'][0] in double_faced):  # Handle DFCs
            print(commander['commanders'][0])
            commander['urls'] = image_lookup[commander['commanders'][0]]
            commander['commanders'] = commander['commanders'][0].split(" // ")
            commander['commanderstring'] = \
                "--".join(normalize_cardnames(commander['commanders']))
        else:
            commander['commanderstring'] = \
                "-".join(sorted(normalize_cardnames(commander['commanders'])))

        # Update user on processing status
        print(commander['commanderstring'])
        processed += 1
        print(f"{processed} / {len(commander_data)}")

    # Save commander names to file
    with open('frontend/commandernames.json', 'w') as commandernames_file:
        json.dump(commander_names, commandernames_file)

    # Sort commanders by decreasing count and save to file
    commander_data.sort(key=lambda commander: -commander['count'])
    with open('frontend/_data/commanders.json', 'w') as commanders_file:
        json.dump(commander_data, commanders_file)

    # Store color popularity (staple) information
    staples = []
    for card in color_popularity:
        if card not in lands:  # Skip lands
            staples.append([card, color_popularity[card][0],
                            image_lookup[card], color_popularity[card][1]])
    # Save color popularity to file
    with open('frontend/_data/staples.json', 'w') as staples_file:
        json.dump(staples, staples_file)
