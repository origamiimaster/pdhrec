"""
Accessing scryfall for card images...
"""
import requests


def get_card_data(card_name):
    card_name = ''.join(char for char in ["+" if c == " " else c for c in card_name.lower()] if char.isalnum() or char == "+")
    url = f"https://api.scryfall.com/cards/named?exact={card_name}"
    r = requests.get(url)
    return r.json()
