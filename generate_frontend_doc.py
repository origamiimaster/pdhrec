import json
from backend.aggregator import get_all_scores
from backend.database import Database
from backend.utils import normalize_text
from backend.update import perform_update, get_latest_bulk_file


if __name__ == "__main__":
    # Initialize the database:
    with open("server-token.json") as f:
        connection_string = json.load(f)['connection']
    database = Database(connection_string)

    path = get_latest_bulk_file(database, directory="scryfall_data")
    with open(path, "r") as f:
        all_card = json.load(f)
    lookup = {}
    double_faces = set()
    for line in all_card:
        try:
            if "image_uris" not in line and "card_faces" in line:
                lookup[line["name"]] = [line["card_faces"][0]["image_uris"]["large"],
                                        line["card_faces"][1]["image_uris"]["large"]]
                double_faces.add(line["name"])
            else:
                lookup[line["name"]] = line["image_uris"]["large"]
        except KeyError:
            continue
        except Exception as e:
            print(e)
            print(json.dumps(line))
            continue
    # Hardcoded to not use the token version of the card.
    lookup["Llanowar Elves"] = "https://cards.scryfall.io/large/front/8/b/8bbcfb77-daa1-4ce5-b5f9-48d0a8edbba9.jpg?1592765148"
    print("Updating database")
    # Commit updates to the database:
    perform_update(database)

    # Returns a list of the commanders / commander pairs, along with their image urls and cleaned names.
    commander_data = {tuple(x['commanders']) for x in database.decks.aggregate(pipeline=[
        {"$match": {"isLegal": True}},
        {"$project": {"_id": 0, "commanders": 1}}
    ])}

    # Sort the names so that we don't double / half count partners
    commander_data = list(set(tuple(sorted(x)) for x in commander_data))

    new_commander_data = []
    for commanders in commander_data:
        urls = []
        for card in commanders:
            new_url = database.cards.find_one({"name": card})['image_urls']
            for url in new_url:
                urls.append(url)
        # print(urls)
        new_commander_data.append({"commanders": commanders, "urls": urls})
    all_synergy_scores, popularity_scores, commander_counts = get_all_scores(database)
    commander_data = new_commander_data
    total = len(commander_data)
    count = 0
    commander_name_data = []
    for item in commander_data:
        print(item)
        commander_name_data.append(" ".join(item["commanders"]))
        # Convert item['commanders'] to a hashable type?
        synergy_scores = all_synergy_scores[tuple(item['commanders'])]

        item["count"] = commander_counts[tuple(item['commanders'])]

        if len(item["commanders"]) == 1 and item["commanders"][0] in double_faces:
            print(item["commanders"][0])
            item["urls"] = lookup[item["commanders"][0]]
            item["commanders"] = [x for x in item["commanders"][0].split(" // ")]
            item['commanderstring'] = "--".join(normalize_text(item['commanders']))
        else:
            item['commanderstring'] = "-".join(sorted(normalize_text(item['commanders'])))
        item['carddata'] = []
        for card in synergy_scores:
            if card in lookup:
                card_image = lookup[card]
            else:
                # print(card)
                card_image = retrieve_card_image(card)
                lookup[card] = card_image
            test = [card, synergy_scores[card], card_image]
            item['carddata'].append(test)
        item['carddata'].sort(key=lambda x: -x[1])
        print(item['commanderstring'])
        count += 1
        print(f"{count} / {total}")


    commander_data.sort(key=lambda x: -x["count"])

    with open("frontend/_data/commanders.json", "w") as f:
        json.dump(commander_data, f)
    with open("frontend/commandernames.json", "w") as f:
        json.dump(commander_name_data, f)
