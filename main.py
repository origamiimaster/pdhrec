from database import save_metadata
from moxfield import get_new_decks
if __name__ == "__main__":
    values = get_new_decks()[0]
    print(values)
    save_metadata({
        "id": values['id'],
        "publicId": values['publicId'],
        "hasPrimer": values['hasPrimer'],
        "name": values['name'],
        "lastUpdatedAtUtc": values['lastUpdatedAtUtc'],
    })
    
