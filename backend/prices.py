"""
Gather prices with MTGJSON and then use them to build prices and TCGPLAYER
affiliate links.  Put them into a json file mapping card name to cheapest
price and url.
"""
import requests, json, gzip, urllib

AFFILIATE_LINK = "https://tcgplayer.pxf.io/c/5127700/1830156/21018"
ALL_PRICES_LINK = "https://mtgjson.com/api/v5/AllPricesToday.json.gz"


def convert_tcg_link_to_affiliate(url_to_encode: str) -> str:
    """
    Convert a url into an affiliate link.
    :param url_to_encode: A string with the TCGplayer url.
    :return: a string with the newly encoded url.
    """
    return AFFILIATE_LINK + "?u=" + urllib.parse.quote(url_to_encode)


def get_zipped_json_from_url(url: str):
    """
    Unzips a file from a destination and reads the JSON in.
    :param url:
    :return:
    """
    r = requests.get(url)
    return json.loads(gzip.decompress(r.content))

def save_price_dictionary(filepath):
    all_printings = get_zipped_json_from_url(
        "https://mtgjson.com/api/v5/AllPrintings.json.gz")["data"]

    print("Got Printings")

    all_prices = get_zipped_json_from_url(
        "https://mtgjson.com/api/v5/AllPricesToday.json.gz")["data"]

    print("Got Prices")

    tcg_player = get_zipped_json_from_url(
        "https://mtgjson.com/api/v5/TcgplayerSkus.json.gz")["data"]

    print("Got TCGplayer SKUs")

    cards_by_name = {}

    # Collate the copies and try and find the cheapest copy of each.
    for set_code in all_printings:
        for card in all_printings[set_code]['cards']:
            if card['name'] not in cards_by_name:
                cards_by_name[card['name']] = None
            uuid = card['uuid']
            name = card['name']
            if uuid in tcg_player and uuid in all_prices:
                # We can link to this version
                productId = tcg_player[uuid][0]['productId']
                try:
                    prices = all_prices[uuid]['paper']['tcgplayer']['retail']['normal']
                    price = prices[list(prices.keys())[0]]
                except KeyError:
                    price = float("inf")

                if cards_by_name[name] is None:
                    cards_by_name[name] = (price, productId)
                else:
                    if price < cards_by_name[name][0]:
                        cards_by_name[name] = (price, productId)

    bad_names = []
    for name in cards_by_name:
        if cards_by_name[name] is None:
            bad_names.append(name)
        elif cards_by_name[name][0] == float("inf"):
            cards_by_name[name] = (None, cards_by_name[name][1])

    for name in bad_names:
        del cards_by_name[name]

    with open(filepath, "w") as f:
        json.dump(cards_by_name, f)



if __name__ == "__main__":
    print("Starting Test")
    print(convert_tcg_link_to_affiliate("https://www.tcgplayer.com/search/magic/product"))



