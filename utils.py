def normalize_text(cards):
    out_cards = []
    for card in cards:
        out_cards.append(''.join(x for x in ["-" if y == " " else y for y in card.lower()] if x.isalnum() or x == "-"))
    return out_cards
