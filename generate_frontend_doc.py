import json
from backend.aggregator import get_all_scores
from backend.database import Database
from backend.utils import normalize_text
from backend.update import perform_update, get_latest_bulk_file


if __name__ == "__main__":
    # Create a connection to the database
    with open("server-token.json") as f:
        connection_string = json.load(f)['connection']
    database = Database(connection_string)

    # Load all cards from bulk json in database
    cards_path = get_latest_bulk_file(database, directory="scryfall_data")
    with open(cards_path, "r") as f:
        all_cards = json.load(f)

    # Create lookup of card images by name, alongside sets of lands and DFCs
    image_lookup = {}
    lands = set()
    double_faces = set()
    for card in all_cards:
        if "Land" in card['type_line']:
            lands.add(card['name'])
        try:
            # Skip tokens
            if "set_type" in card and card['set_type'] == "token":
                continue
            # Double-faced cards
            if "image_uris" not in card and "card_faces" in card:
                image_lookup[card["name"]] = \
                    [card["card_faces"][0]["image_uris"]["large"],
                     card["card_faces"][1]["image_uris"]["large"]]
                double_faces.add(card["name"])
            # Single-faced cards
            else:
                image_lookup[card["name"]] = card["image_uris"]["large"]
        # TODO: More robust error handling
        except KeyError: # Why isn't this handled with other exceptions?
            continue
        except Exception as e:
            print(e)
            print(json.dumps(card))
            continue

    # Commit updates to the database
    print("Updating datasbase")
    perform_update(database)

    # Generate a list of the commanders / commander pairs, along with their 
    # image urls and cleaned names
    commander_data = {tuple(deck['commanders']) 
                      for deck in database.decks.aggregate(pipeline=[
                          {"$match": {"isLegal": True}}, 
                          {"$project": {"_id": 0, "commanders": 1}}
                          ])}
    # Ensure commanders are unique (sort pairs)
    commander_data = list(set(tuple(sorted(x)) for x in commander_data))

    # Store all updated commander data
    new_commander_data = []
    # Record commander names and image URLs
    for commanders in commander_data:
        urls = []
        for card in commanders:
            new_url = database.cards.find_one({"name": card})['image_urls']
            for url in new_url:
                urls.append(url)
        # print(urls)
        new_commander_data.append({"commanders": commanders, "urls": urls})
    
    # Record all other commander statistics
    all_synergy_scores, popularity_scores, commander_counts, \
        color_popularity = get_all_scores(database)
    processed = 0 # Number of commanders processed
    new_commander_names = []
    for commander in new_commander_data:
        print(f"Updating: {commander}")
        # Store commander name
        new_commander_names.append(" ".join(commander["commanders"]))
        # Store commander count
        commander["count"] = commander_counts[tuple(commander['commanders'])]
        # Parse commanderstring (for database use)
        if (len(commander["commanders"]) == 1 
            and commander["commanders"][0] in double_faces): # Handle DFCs
            print(commander["commanders"][0])
            commander["urls"] = image_lookup[commander["commanders"][0]]
            commander["commanders"] = commander["commanders"][0].split(" // ")
            commander['commanderstring'] = "--".join(normalize_text(commander['commanders']))
        else: # Handle single-faced and partner commanders
            commander['commanderstring'] = "-".join(sorted(normalize_text(commander['commanders'])))
    
    # Save commander names to file
    with open("frontend/commandernames.json", "w") as f:
        json.dump(new_commander_names, f)

        # Store synergy scores
        # TODO: Convert item['commanders'] to a hashable type?
        synergy_scores = all_synergy_scores[tuple(commander['commanders'])]
        commander['carddata'] = []
        for card in synergy_scores:
            if card in image_lookup:
                card_image = image_lookup[card]
            else: 
                raise Exception(f"{card} not in image_lookup")
            card_info = [card, synergy_scores[card], card_image]
            commander['carddata'].append(card_info)
        # Sort cards by decreasing synergy scores
        commander['carddata'].sort(key=lambda x: -x[1])

        # Update user on processing status
        print(commander['commanderstring'])
        processed += 1
        print(f"{processed} / {len(new_commander_data)}")

    # Sort commanders by decreasing count and save to file
    new_commander_data.sort(key=lambda x: -x["count"])
    with open("frontend/_data/commanders.json", "w") as f:
        json.dump(new_commander_data, f)

    # Store color popularity (staple) information
    new_color_popularity = []
    for cardname in color_popularity:
        if cardname in lands: # Skip lands
            continue
        try:
            commander = [cardname, color_popularity[cardname][0], 
                         image_lookup[cardname], color_popularity[cardname][1]]
            new_color_popularity.append(commander)
        except Exception as e: # TODO: More robust?
            print(e)
            print(cardname)
    # Save color popularity to file
    with open("frontend/_data/staples.json", "w") as f:
        json.dump(new_color_popularity, f)
