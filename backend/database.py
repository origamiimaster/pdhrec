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

    def insert_deck(self, data: dict, card_cache: dict | None = None) -> None:
        """
        Insert the data for a deck into the database.

        :param data: Data for a deck, as a dictionary from a Deck object
        :param card_cache: Optional dictionary cache of card names to avoid duplicate inserts
        """
        self.decks.update_one(filter={'_id': data['_id']},
                              update={'$set': data}, upsert=True)

        # Create blank cache if none provided
        if card_cache is None:
            card_cache = {}

        for card in set(data['cards']):
            if card not in card_cache:
                self.insert_card({'name': card, 'needsUpdate': True})

        for card in data['commanders']:
            if card not in card_cache:
                self.insert_card({'name': card, 'needsUpdate': True})

    def update_card(self, card_data: dict, upsert: bool = True) -> None:
        """
        Updates a card object into the database. If upsert is true, it will
        insert the card. If not, the function will make no change
        to the database.

        :param card_data: The card to insert. Must have a name.
        :param upsert: boolean flag if you want to insert as well.
        """
        assert 'name' in card_data
        if "needsUpdate" in card_data and not card_data['needsUpdate']:
            card_data['updated'] = time()
            self.cards_cache.append(card_data['name'])

        res = self.cards.update_one(filter={'name': card_data['name']},
                                    update={'$set': card_data}, upsert=upsert)

    def insert_card(self, card_data: dict) -> bool:
        """
        Insert a new card object into the "cards" collection.  Returns
        success or failure.

        :param card_data: The card to insert.
        :return: if the value was inserted.
        """
        assert 'name' in card_data
        try:
            res = self.cards.insert_one(card_data)
            return True
        except pymongo.errors.DuplicateKeyError:
            return False

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
