"""
Gather prices with MTGJSON and then use them to build prices and TCGPLAYER
affiliate links.  Put them into a json file mapping card name to cheapest
price and url.
"""
import requests, json, gzip, urllib
from backend.utils import normalize_cardname

ILLEGAL_SETS = ["Collectors Ed", 'Magic 30th Anniversary Edition', 'World Championships']

TCGPLAYER_AFFILIATE_LINK = "https://partner.tcgplayer.com/c/5127700/1830156/21018"
TCGPLAYER_ALL_PRICES_LINK = "https://mtgjson.com/api/v5/AllPricesToday.json.gz"

CARDKINGDOM_AFFILIATE_LINK = "?partner=PDHREC&partner_args="
CARDKINGDOM_PRICES_LINK = "https://api.cardkingdom.com/api/pricelist" # "https://api.cardkingdom.com/api/v2/pricelist"


def convert_tcg_link_to_affiliate(url_to_encode: str) -> str:
    """
    Convert a url into an affiliate link.
    :param url_to_encode: A string with the TCGplayer url.
    :return: a string with the newly encoded url.
    """
    return TCGPLAYER_AFFILIATE_LINK + "?u=" + urllib.parse.quote(url_to_encode)


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

    r = requests.get(CARDKINGDOM_PRICES_LINK)
    card_kingdom_data = r.json()['data']

    cards_by_name = {}

    # Collate the copies and try and find the cheapest copy of each.
    for set_code in all_printings:
        set_name = normalize_cardname(all_printings[set_code]["name"])
        for card in all_printings[set_code]['cards']:
            if card['name'] not in cards_by_name:
                cards_by_name[card['name']] = None
            uuid = card['uuid']
            name = card['name']
            if uuid in tcg_player and uuid in all_prices:
                # We can link to this version
                productId = tcg_player[uuid][0]['productId']
                try:
                    tcg_prices = all_prices[uuid]['paper']['tcgplayer']['retail']['normal']
                    tcg_price = tcg_prices[list(tcg_prices.keys())[0]]
                except KeyError:
                    tcg_price = float("inf")

                # try:
                #     cardkingdom_prices = all_prices[uuid]['paper']['cardkingdom']['retail']['normal']
                #     cardkingdom_price = cardkingdom_prices[list(cardkingdom_prices.keys())[0]]
                # except KeyError:
                #     cardkingdom_price = float("inf")

                # try:
                #     card_name = normalize_cardname(card['name'])
                #     cardkingdom_url = f"https://cardkingdom.com/mtg/{set_name}/{card_name}"
                # except Exception as e:
                #     print(e)
                #     card_name = "ERROR"
                #     cardkingdom_url = "ERROR"

                if cards_by_name[name] is None:
                    # cards_by_name[name] = (tcg_price, productId, cardkingdom_price, cardkingdom_url)
                    cards_by_name[name] = (tcg_price, productId)
                else:
                    if tcg_price < cards_by_name[name][0]:
                        # cards_by_name[name] = (tcg_price, productId, cardkingdom_price, cardkingdom_url)
                        cards_by_name[name] = (tcg_price, productId)

    bad_names = []
    for name in cards_by_name:
        if cards_by_name[name] is None:
            bad_names.append(name)
        else:
            if cards_by_name[name][0] == float("inf"):
                # cards_by_name[name] = (None, cards_by_name[name][1], cards_by_name[name][2], cards_by_name[name][3])
                cards_by_name[name] = (None, cards_by_name[name][1])
            # if cards_by_name[name][2] == float("inf"):
            #     cards_by_name[name] = (cards_by_name[name][0], cards_by_name[name][1], None, cards_by_name[name][3])

    for name in bad_names:
        del cards_by_name[name]

    # card_kingdom_data = {x['name']: (x['price_retail'], x['url']) for x in card_kingdom_data}
    new_card_kingdom_data = {}
    for card in card_kingdom_data:
        card_name = card['name']
        card_price = card['price_retail']
        card_url = card['url']
        # We only care about cards that are in stock, and not a world championship version.
        if card["qty_retail"] != 0 and card["edition"] not in ILLEGAL_SETS:
            # Debugging purposes only:
            if card_name == "Ponder":
                print(card['name'], card['url'], card['price_retail'], card['edition'])
            if card_name not in new_card_kingdom_data:
                new_card_kingdom_data[card_name] = (card_price, card_url)
            else:
                if float(new_card_kingdom_data[card_name][0]) > float(card_price):
                    new_card_kingdom_data[card_name] = (card_price, card_url)
    print(new_card_kingdom_data['Ponder'])

    for name in cards_by_name:
        try:
            cards_by_name[name] = (cards_by_name[name][0], cards_by_name[name][1], new_card_kingdom_data[name][0], new_card_kingdom_data[name][1])
        except KeyError:
            cards_by_name[name] = (cards_by_name[name][0], cards_by_name[name][1], None, None)

    with open(filepath, "w") as f:
        json.dump(cards_by_name, f)



if __name__ == "__main__":
    # print("Starting Test")
    # print(convert_tcg_link_to_affiliate("https://www.tcgplayer.com/search/magic/product"))

    save_price_dictionary("../frontend/_data/")

