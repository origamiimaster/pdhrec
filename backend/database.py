"""
Restarting database, with better design.
Database is a Atlas MongoDB database, intended to be used to periodically generate a static website, rather than for
immediate use.
"""
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
        Given the data for a particular deck, it takes it and inserts into the database.
        :return: None
        """
        cards_to_insert = {card for card in data['cards'] if card not in self.cards_cache}
        self.decks.update_one(filter={"_id": data['_id']}, update={"$set": data}, upsert=True)
        for card in cards_to_insert:
            self.insert_card({"name": card, "needsUpdate": True})
        for card in data['commanders']:
            if card not in self.cards_cache:
                self.insert_card({"name": card, "needsUpdate": True})

    def get_deck(self, deck_id) -> object:
        """
        Returns a particular deck given the data.
        :param deck_id:
        :return:
        """
        res = self.cards.find_one({"_id": deck_id})
        return res

    def insert_card(self, card_data, insert_many=False) -> None:
        """
        Inserts a card into the database.
        :param card_data:
        :return: None
        """
        assert "name" in card_data
        res = self.cards.update_one({"name": card_data['name']}, {"$set": card_data}, upsert=True)
        self.cards_cache.append(card_data["name"])
        return res

    def get_card(self, card_id) -> object:
        """
        Gets a card from the database and returns it.
        :param card_id:
        :return:
        """
        res = self.cards.find_one({"name": card_id})
        return res


if __name__ == "__main__":
    print("Starting")
    with open("../server-token.json") as f:
        connection_string = json.load(f)['connection']
    database = Database(connection_string)

