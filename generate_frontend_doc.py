# from pymongo import MongoClient
import json
from backend.azure_database import new_get_all_commander_counts, get_new_synergy_scores, retrieve_card_image


if __name__ == "__main__":
    with open("oracle-cards-20220903090217.json", "r") as f:
        all_card = json.load(f)
    lookup = {}
    double_faces = set()
    for line in all_card:
        try:
            if "image_uris" not in line and "card_faces" in line:
                lookup[line["name"]] = [line["card_faces"][0]["image_uris"]["large"], line["card_faces"][1]["image_uris"]["large"]]
                double_faces.add(line["name"])
            else:
                lookup[line["name"]] = line["image_uris"]["large"]
        except Exception as e:
            print(e)
            print(json.dumps(line))
            continue
    # Hardcoded to not use the token version of the card.
    lookup["Llanowar Elves"] = "https://cards.scryfall.io/large/front/8/b/8bbcfb77-daa1-4ce5-b5f9-48d0a8edbba9.jpg?1592765148"



    commander_data = new_get_all_commander_counts()
    total = len(commander_data)
    count = 0
    commander_name_data = []
    for item in commander_data:
        commander_data.append(" ".join(item["commanders"]))
        if len(item["commanders"])== 1 and item["commanders"][0] in double_faces:
            print(item["commanders"][0])
            item["urls"] = lookup[item["commanders"][0]]
            item["commanders"] = [x for x in item["commanders"][0].split(" // ")]
            # item["commanderstring"] = item["commanderstring"].replace("--", "-")
            # print(item)
            # exit(1)
        synergy_scores = get_new_synergy_scores(item['commanderstring'])
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
        count += 1
        print(f"{count} / {total}")

    commander_data.sort(key=lambda x: -x["count"])

    # print(commander_data)

    with open("frontend/_data/commanders.json", "w") as f:
        json.dump(commander_data, f)
    with open("frontend/commandernames.json", "w") as f:
        json.dump(commander_name_data)
