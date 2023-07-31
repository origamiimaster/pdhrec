from typing import List


def normalize_cardnames(cards: List[str]) -> List[str]:
    return map(normalize_cardname, cards)


def normalize_cardname(cardname: str, sep="-"):
    return ''.join(char for char in cardname.lower().replace(' ', sep) 
                   if char.isalnum() or char == sep)
