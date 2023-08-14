"""
Unit tests for the Moxfield API / DeckSource
"""
from backend.moxfield import MoxfieldDeckSource


def test_get_deck_empty() -> None:
    """
    Test if the function MoxfieldDeckSource.get_decks(id)
    """
    source = MoxfieldDeckSource()
    deck_id = "yH7w5QHvCEKJSjdnrzr1EQ"
    deck = source.get_deck(deck_id)
    assert len(deck['commanders']) == 0
    assert len(deck['cards']) == 0
    assert deck_id == deck['_id']
    assert deck == {
        '_id': 'yH7w5QHvCEKJSjdnrzr1EQ', 'update_date': 1691549744.723,
        'commanders': [], 'cards': []
    }


def test_get_deck_invalid_id() -> None:
    source = MoxfieldDeckSource()
    deck_id = "NOT-VALID-ID"
    deck = source.get_deck(deck_id)
    assert deck is None


if __name__ == "__main__":
    test_get_deck_empty()
    test_get_deck_invalid_id()
    print("Tests Passed")
