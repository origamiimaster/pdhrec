"""
Database is a Atlas MongoDB database, intended to be used to periodically
generate a static website, rather than for immediate use.
"""
from typing import Any
from time import time
import json
import pymongo

class Database:
    """
    Class representing the operations allowed for the database.
    """
    def __init__(self, connection_string: str):
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client["pdhrec"]
        self.cards = self.db["cards"]
        self.decks = self.db["decks"]
        self.cards_cache = [x['name'] for x in self.cards.aggregate(pipeline=[{"$project": {"_id": 0, "name": 1}}])]

    def insert_deck(self, data) -> None:
        """
        Insert the data for a particular deck into the database.
        """
        self.decks.update_one(filter={"_id": data['_id']}, 
                              update={"$set": data}, upsert=True)
        cards_to_insert = set(card for card in data['cards'] 
                              if card not in self.cards_cache)
        for card in cards_to_insert:
            self.insert_card({"name": card, "needsUpdate": True})
        for card in data['commanders']:
            if card not in self.cards_cache:
                self.insert_card({"name": card, "needsUpdate": True})

    def get_deck(self, deck_id) -> Any:
        """
        Return the deck with the given ID.
        """
        return self.cards.find_one({"_id": deck_id})

    def insert_card(self, card_data) -> None:
        """
        Insert a card into the database.
        """
        assert "name" in card_data
        if not card_data["needsUpdate"]:
            card_data['updated'] = time()
        self.cards_cache.append(card_data["name"])
        return self.cards.update_one({"name": card_data['name']}, 
                                     {"$set": card_data}, upsert=True)

    def get_card(self, card_id) -> object:
        """
        Return a card from the database.
        """
        return self.cards.find_one({"name": card_id})


if __name__ == "__main__":
    print("Starting")
    with open("../server-token.json") as server_token_file:
        connection_string = json.load(server_token_file)['connection']
    database = Database(connection_string)

