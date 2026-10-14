import json
from backend.aggregator import get_all_scores, get_card_color_identities
from backend.database import MongoDatabase
from backend.moxfield import MoxfieldDeckSource
from backend.archidekt import ArchidektDeckSource
from backend.prices import save_price_dictionary
from backend.utils import normalize_cardnames
from backend.update import perform_update, get_latest_bulk_file
import tqdm

# with open('server-token.json') as server_token_file:
#     connection_string = json.load(server_token_file)['connection']

# database = MongoDatabase(connection_string)
sources = [ArchidektDeckSource(), MoxfieldDeckSource()]

results = sources[0].get_new_decks_paginated(1)

# # Commit updates to the database
# print('Updating database')
# perform_update(database, sources)
