# from pymongo import MongoClient
import json
from azure_database import new_get_all_commander_counts, get_new_synergy_scores, retrieve_card_image

if __name__ == "__main__":
    with open("oracle-cards-20220903090217.json", "r") as f:
        all_card = json.load(f)
    lookup = {}

    for line in all_card:
        try:
            if "card_faces" in line:
                lookup[line["name"]] = line["card_faces"][0]["image_uris"]["large"]
            else:
                lookup[line["name"]] = line["image_uris"]["large"]
        except Exception as e:
            print(e)
            continue


    commander_data = new_get_all_commander_counts()
    total = len(commander_data)
    count = 0
    for item in commander_data:
        # print(item)
        synergy_scores = get_new_synergy_scores(item['commanderstring'])

        # print(synergy_scores)
        item['carddata'] = []
        for card in synergy_scores:
            # print(f"item: {card}")
            # print(f"score: {synergy_scores[card]}")
            if card in lookup:
                card_image = lookup[card]
            else:
                card_image = retrieve_card_image(card)
                lookup[card] = card_image
            test = [card, synergy_scores[card], card_image]
            item['carddata'].append(test)
        item['carddata'].sort(key=lambda x: -x[1])
        count += 1
        print(f"{count} / {total}")

    commander_data.sort(key=lambda x: -x["count"])
    with open("frontend/_data/commanders.json", "w") as f:
        json.dump(commander_data, f)
