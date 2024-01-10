"""
Database is an Atlas MongoDB database, intended to be used to periodically
generate a static website, rather than for immediate use.
"""
from time import time
import json
import pymongo


class MongoDatabase:
    """
    Class representing the operations allowed for the database.

    client: MongoClient to a Mongo database
    database: PDHREC database in MongoClient
    cards: cards table in PDHREC database
    decks: decks table in PDHREC database
    cards_cache: In-memory cache of named of updated cards in database
    """

    def __init__(self, connection_string: str):
        self.client = pymongo.MongoClient(connection_string)
        self.database = self.client['pdhrec']
        self.cards = self.database['cards']
        self.decks = self.database['decks']
        cache_pipeline = [{'$match': {'needsUpdate': False}},
                          {'$project': {'_id': 0, 'name': 1}}]
        self.cards_cache = [card['name'] for card in
                            self.cards.aggregate(pipeline=cache_pipeline)]

    def insert_deck(self, data: dict) -> None:
        """
        Insert the data for a deck into the database.

        :param data: Data for a deck, as a dictionary from a Deck object
        """
        self.decks.update_one(filter={'_id': data['_id']},
                              update={'$set': data}, upsert=True)
        for card in set(data['cards']):
            self.insert_card({'name': card, 'needsUpdate': True})
        for card in data['commanders']:
            self.insert_card({'name': card, 'needsUpdate': True})

    def insert_card(self, card_data: dict) -> None:
        """
        Insert a card into the database.
        If the card is already present in card_cache, do nothing.

        :param card_data: Card to insert, as a dictionary from a Card object
        """
        assert 'name' in card_data

        self.cards.update_one(filter={'name': card_data['name']},
                              update={'$set': card_data}, upsert=True)
        if not card_data['needsUpdate']:
            card_data['updated'] = time()
            self.cards_cache.append(card_data['name'])

    def get_card(self, card: str) -> dict:
        """
        Return the database entry on a card of the given name.

        :param card: Name of card to query
        :return: Database entry of the card as a dictionary of card attributes
        """
        return self.cards.find_one({'name': card})


if __name__ == '__main__':
    print('Starting')
    with open('../server-token.json') as server_token_file:
        test_connection_string = json.load(server_token_file)['connection']
    test_database = MongoDatabase(test_connection_string)
