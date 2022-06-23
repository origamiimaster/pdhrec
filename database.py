"""
Store and load data saved by the project.

Three main collections will be use: 
1. Deck metadata. Has deck been updated? Other details...
2. Deck Cards: For each deck, what cards does it run? Is it legal?
3. Commander Cards: For each commander, what cards does it run? In what quantities?
"""
from pymongo import MongoClient

client = MongoClient()


def save_metadata(data):
    print(data)
    index = data['publicId']
    db = client['pdhrec']
    col = db['metadata']
    col.insert_one(data)
    # print(client.list_database_names())
    


def save_cards(data):
    index = data['publicId']

def insert_new_commander_data(data):
    pass

def update_commander_data(old_data, new_data):
    pass




if __name__ == "__main__":
    save_metadata({"publicId": "0"})