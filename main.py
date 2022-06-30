import time

from dateutil import parser

from azure_database import save_metadata, load_metadata, save_cards, get_ids_need_update, get_all_metadata, get_newest_metadata
from moxfield import get_deck_data, get_new_decks

def smart_update():
    data = get_all_metadata()
    new_decks = get_new_decks()
    last_time_update = get_newest_metadata() # ['lastUpdatedAtUtc']
    newest_deck = new_decks[0]  # Information is received in sorted order.
    # Check if the newest deck is newer than the current newest:
    print("Comparing Times")
    newest_time = parser.parse(newest_deck['lastUpdatedAtUtc']).timestamp()
    if last_time_update < newest_time:
        print("Updating")
        # Iterate backwards over the new decks, incrementing page count until we pass the right place
        time_to_reach = last_time_update
        last_deck_time = newest_time
        page = 1
        while time_to_reach < last_deck_time:
            for deck in new_decks:
                print(f"Saving deck {deck['name']}")
                save_metadata({
                    "id": deck['id'],
                    "publicId": deck['publicId'],
                    "hasPrimer": deck['hasPrimer'],
                    "name": deck['name'],
                    "needsUpdate": True,
                    "lastUpdatedAtUtc": parser.parse(deck['lastUpdatedAtUtc']).timestamp(),
                })
                last_deck_time = parser.parse(deck['lastUpdatedAtUtc']).timestamp()
                if time_to_reach >= last_deck_time:
                    break  # Reached exit conditions
            page += 1
            time.sleep(1)
            new_decks = get_new_decks(page)
    else:
        print("No new decks")


if __name__ == "__main__":
    # Check if there's anything in the database.  If not, add one so we can smart update.
    if len([x for x in get_all_metadata()]) == 0:
        deck = get_new_decks(60)[-1]
        # deck = get_new_decks(1)[-1]
        save_metadata({
            "id": deck['id'],
            "publicId": deck['publicId'],
            "hasPrimer": deck['hasPrimer'],
            "name": deck['name'],
            "needsUpdate": True,
            "lastUpdatedAtUtc": parser.parse(deck['lastUpdatedAtUtc']).timestamp(),
        })
    while True:
        smart_update()
        for public_id in get_ids_need_update():
            card_data = get_deck_data(public_id)
            if card_data is not False:
                save_cards(card_data)
            data = load_metadata(public_id)
            data['needsUpdate'] = False
            save_metadata(data)
        time.sleep(60 * 10)
