"""
Records data for the project in a database, to be accessed later.
"""

import os.path
import random
import time

from dateutil import parser
import requests
from moxfield import get_deck_data

database_keys = ['matchTypes', 'matchedCards', 'id', 'name', 'hasPrimer', 'format', 'areCommentsEnabled', 'visibility',
                 'publicUrl', 'publicId', 'likeCount', 'viewCount', 'commentCount', 'isLegal', 'authorsCanEdit',
                 'isShared', 'mainCardId', 'mainCardIdIsCardFace', 'createdByUser', 'authors', 'createdAtUtc',
                 'lastUpdatedAtUtc', 'mainboardCount', 'sideboardCount', 'maybeboardCount', 'hubNames', 'cardsUpdated']

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = "1HRUPrElZTYd4S9L6-paIZQy9hdWYPmHzIWz1-Dbp35U"
SAMPLE_RANGE_NAME = "Data"


def init_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        try:
            service = build('sheets', 'v4', credentials=creds)
            return service
        except HttpError as err:
            print(err)


def insert_row(row):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)
        # print(service)
        val = service.spreadsheets().values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME,
                                                     valueInputOption="USER_ENTERED",
                                                     body={"values": [row]}).execute()
        # print(val)
    except HttpError as err:
        print(err)

def insert_row_generic(row, sheet):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)
        # print(service)
        val = service.spreadsheets().values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                                     range=sheet,
                                                     valueInputOption="USER_ENTERED",
                                                     body={"values": [row]}).execute()
        # print(val)
    except HttpError as err:
        print(err)



def update_row_generic(row, row_num, sheet):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)
        # print(service)
        val = service.spreadsheets().values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                                     range=sheet + '!' + str(row_num) + ":" + str(row_num),
                                                     valueInputOption="USER_ENTERED",
                                                     body={"values": [row]}).execute()
        # print(val)
    except HttpError as err:
        print(err)


def update_row(row, row_num):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)
        # print(service)
        val = service.spreadsheets().values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                                     range=SAMPLE_RANGE_NAME + '!' + str(row_num) + ":" + str(row_num),
                                                     valueInputOption="USER_ENTERED",
                                                     body={"values": [row]}).execute()
        # print(val)
    except HttpError as err:
        print(err)


def write_deck_row(row, row_num):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)
        val = service.spreadsheets().values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                                     range="Cards" + '!' + str(row_num) + ":" + str(row_num),
                                                     valueInputOption="USER_ENTERED",
                                                     body={"values": [row]}).execute()
    except HttpError as err:
        print(err)


def read_rows():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        return values
    except HttpError as err:
        print(err)


def read_data_rows():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range="Cards").execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        return values
    except HttpError as err:
        print(err)


card_rows_headers = ['id', 'name', 'description', 'format', 'visibility', 'publicUrl', 'publicId', 'likeCount',
                     'viewCount', 'commentCount', 'areCommentsEnabled', 'isShared', 'authorsCanEdit', 'createdByUser',
                     'authors', 'requestedAuthors', 'main', 'mainboardCount', 'mainboard', 'sideboardCount',
                     'sideboard', 'maybeboardCount', 'maybeboard', 'commandersCount', 'commanders', 'companionsCount',
                     'companions', 'version', 'signatureSpellsCount', 'signatureSpells', 'tokens', 'hubs',
                     'createdAtUtc', 'lastUpdatedAtUtc', 'exportId', 'authorTags', 'isTooBeaucoup']
card_rows_headers_2 = ["cards"] + [str(x + 1) for x in range(100)]


class Database:

    def __init__(self):
        self.cached = read_rows()
        self.ids = [x[database_keys.index('id')] for x in self.cached]
        self.cards_cached = read_data_rows()
        self.last_time_update = max(
            [parser.parse(x[database_keys.index('lastUpdatedAtUtc')]).timestamp() for x in self.cached[1:]])

    def update_deck(self, deck):
        print("Updating deck:")
        print(deck)
        row = [str(deck[key]) for key in database_keys[:-1]] + [str(False)]
        if deck['id'] in self.ids:
            print("Deck exists in database, updating")
            print(f"Row to update is {self.ids.index(deck['id']) + 1}")
            update_row(row, self.ids.index(deck['id']) + 1)
            self.cached[self.ids.index(deck['id'])] = row
        else:
            print("Deck does not exist in database, adding")
            insert_row(row)
            self.cached.append(row)
            self.ids.append(str(deck['id']))
        self.last_time_update = max(parser.parse(str(deck['lastUpdatedAtUtc'])).timestamp(), self.last_time_update)

    def get_deck(self, deck_id):
        if deck_id in self.ids:
            return self.cached[self.ids.index(deck_id)]
        else:
            return 0

    def smart_update(self):
        new_decks = get_new_decks()
        newest_deck = new_decks[0]  # Information is received in sorted order.
        # Check if the newest deck is newer than the current newest:
        print("Comparing Times")
        newest_time = parser.parse(newest_deck['lastUpdatedAtUtc']).timestamp()
        if self.last_time_update < newest_time:
            print("Updating")
            # Iterate backwards over the new decks, incrementing page count until we pass the right place
            time_to_reach = self.last_time_update
            last_deck_time = newest_time
            page = 1
            while time_to_reach < last_deck_time:
                for deck in new_decks:
                    self.update_deck(deck)
                    last_deck_time = parser.parse(deck['lastUpdatedAtUtc']).timestamp()
                    if time_to_reach >= last_deck_time:
                        break  # Reached exit conditions
                page += 1
                new_decks = get_new_decks(page)


        else:
            print("No new decks")
            # We have the latest pauper edh decks.

    def get_all_decks(self):
        return self.cached

    def save_all_deck_data(self):
        for value in self.cached[1:]:
            if value[database_keys.index('cardsUpdated')] != "TRUE":
                self.save_deck_data(value[database_keys.index("publicId")])
                # time.sleep(60 + random.random() * 60)
                time.sleep(1)

    def save_deck_data(self, publicId):
        deck = get_deck_data(publicId)

        # Put that information into the database....
        if deck is False:
            print("Deck made private")
            index = [x[9] for x in self.cached].index(publicId)
            self.cached[index][database_keys.index('cardsUpdated')] = str(True)
            self.cached[index][database_keys.index('visibility')] = "?"
            update_row(self.cached[index], index + 1)
            return
        # row = []
        # for key in card_rows_headers:
        #     if key in ['mainboard', 'sideboard', 'maybeboard', 'tokens', 'authorTags']:
        #         row.append("N/A")
        #         continue
        #     row.append(str(deck[key]))
        #
        # if check_deck_legal(deck):
        #     for card in deck['mainboard']:
        #         row.append(str({card: deck['mainboard'][card]['quantity']}))
        # else:
        #     print("Deck is not legal")
        # for _ in range(138 - len(row)):
        #     row.append("N/A")
        #
        index = self.ids.index(deck['id'])
        # while len(self.cards_cached) < index + 1:
        #     self.cards_cached.append([])
        # self.cards_cached[index] = row
        # write_deck_row(row, index + 1)

        if check_deck_legal(deck):
            self.load_cards_to_commander(deck)

        # set cardsUpdated to TRUE
        self.cached[index][database_keys.index('cardsUpdated')] = str(True)
        update_row(self.cached[index], index + 1)

    def load_cards_to_commander(self, deck):
        # print(deck)
        row = ["Count", str(1)]
        for card in deck['commanders']:
            row.append(card)
        if len(deck['commanders']) == 1:
            row.append("N/A")
        else:
            row[2:] = sorted(row[2:])
        old_rows = get_old_commander_row()
        old_row = None
        if row[2:] in [[my_row[2], my_row[3]] if len(my_row) >= 4 else None for my_row in old_rows]:
            old_row = old_rows[[[my_row[2], my_row[3]] for my_row in old_rows].index(row[2:])]
        if old_row is None:
            for card in deck['mainboard']:
                row.append(card)
                row.append(str(1))
            insert_row_generic(row, "Commanders")
        else:
            for card in deck['mainboard']:
                if card in old_row[2:]:
                    old_row[old_row.index(card) + 1] = int(old_row[old_row.index(card) + 1]) + 1
                else:
                    old_row.append(card)
                    old_row.append(str(1))
            old_row[1] = int(old_row[1]) + 1
            update_row_generic(old_row, [[my_row[2], my_row[3]] for my_row in old_rows].index(row[2:4]) + 1, "Commanders")
        old_row = old_rows[0]
        for card in deck['mainboard']:
            if card in old_row[2:]:
                old_row[old_row.index(card) + 1] = int(old_row[old_row.index(card) + 1]) + 1
            else:
                old_row.append(card)
                old_row.append(str(1))
        old_row[1] = int(old_row[1]) + 1
        update_row_generic(old_row, 1, "Commanders")


def get_old_commander_row():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range="Commanders").execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        return values
    except HttpError as err:
        print(err)


def load_initial_decks():
    decks = get_new_decks()
    for deck in decks:
        insert_val = []
        for key in database_keys:
            insert_val.append(str(deck[key]))
        insert_row(insert_val)


def check_deck_legal(deck):
    if deck['mainboardCount'] != 100:
        return False
    if len(deck['commanders']) == 0 or len(deck['commanders']) > 2:
        return False
    for card_name in deck['commanders']:
        if deck['commanders'][card_name]['card']['legalities']['paupercommander'] == "not_legal":
            return False
        if deck['commanders'][card_name]['card']['legalities']['paupercommander'] == "restricted":
            pass  # expected condition
        if deck['commanders'][card_name]['card']['legalities']['paupercommander'] == "legal":
            # Stuff gets complicated here.  If the card was printed at common, but also at uncommon,
            # and is a creature, we allow it.  If the card was printed at common, but not uncommon, we don't allow it.
            # We also will disallow common backgrounds for now, but mainly cause it's easier this way not any other
            # reason.
            if deck['commanders'][card_name]['card']['rarity'] == "uncommon":
                pass
            else:
                return False
    # Now that the commanders are done, we check the cards in the rest of the deck:
    for card_name in deck['mainboard']:
        if deck['mainboard'][card_name]["card"]['legalities']['paupercommander'] == "legal":
            pass
        else:
            return False
    # every card in the deck is checked, everything validated
    return True


def get_new_decks(page=1):
    url = f"""https://api.moxfield.com/v2/decks/search?pageNumber={page}&pageSize=64&sortType=updated&sortDirection=Descending&fmt=pauperEdh&board=mainboard"""
    r = requests.get(url)
    print(r)
    return r.json()['data']


if __name__ == "__main__":
    db = Database()

    while True:
        print("Smart Updating")
        db.smart_update()
        print("Updating Decks")
        db.save_all_deck_data()
        time.sleep(60 + random.random() * 60)
