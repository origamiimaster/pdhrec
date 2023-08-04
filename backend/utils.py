from typing import List, Iterable


# Useful lists related to all pair commanders
partner_commanders = {"Alena, Kessig Trapper",
                      "Alharu, Solemn Ritualist",
                      "Anara, Wolvid Familiar",
                      "Ardenn, Intrepid Archaeologist",
                      "Armix, Filigree Thrasher",
                      "Breeches, Brazen Plunderer",
                      "Brinelin, the Moon Kraken",
                      "Dargo, the Shipwrecker",
                      "Esior, Wardwing Familiar",
                      "Falthis, Shadowcat Familiar",
                      "Ghost of Ramirez DePietro",
                      "Gilanra, Caller of Wirewood",
                      "Glacian, Powerstone Engineer",
                      "Halana, Kessig Ranger",
                      "Ich-Tekik, Salvage Splicer",
                      "Kediss, Emberclaw Familiar",
                      "Keleth, Sunmane Familiar",
                      "Keskit, the Flesh Sculptor",
                      "Malcolm, Keen-Eyed Navigator",
                      "Miara, Thorn of the Glade",
                      "Nadier, Agent of the Duskenel",
                      "Numa, Joraga Chieftain",
                      "Prava of the Steel Legion",
                      "Radiant, Serra Archangel",
                      "Rebbec, Architect of Ascension",
                      "Rograkh, Son of Rohgahh",
                      "Siani, Eye of the Storm",
                      "Slurrk, All-Ingesting",
                      "Toggo, Goblin Weaponsmith",
                      "Tormod, the Desecrator"}

partner_pairs = [{"Blaring Captain", "Blaring Recruiter"},
                 {"Chakram Retriever", "Chakram Slinger"},
                 {"Impetuous Protege", "Proud Mentor"},
                 {"Ley Weaver", "Lore Weaver"},
                 {"Soulblade Corrupter", "Soulblade Renewer"}]

background_commanders = {"Abdel Adrian, Gorion's Ward",
                         "Alora, Merry Thief",
                         "Amber Gristle O'Maul",
                         "Ellyn Harbreeze, Busybody",
                         "Erinis, Gloom Stalker",
                         "Ganax, Astral Hunter",
                         "Gut, True Soul Zealot",
                         "Halsin, Emerald Archdruid",
                         "Imoen, Mystic Trickster",
                         "Livaan, Cultist of Tiamat",
                         "Lulu, Loyal Hollyphant",
                         "Rasaad yn Bashir",
                         "Renari, Merchant of Marvels",
                         "Safana, Calimport Cutthroat",
                         "Sarevok, Deathbringer",
                         "Sivriss, Nightmare Speaker",
                         "Skanos Dragonheart",
                         "Vhal, Candlekeep Researcher",
                         "Viconia, Drow Apostate",
                         "Wilson, Refined Grizzly"}

backgrounds = {"Acolyte of Bahamut",
               "Agent of the Iron Throne",
               "Agent of the Shadow Thieves",
               "Cloakwood Hermit",
               "Criminal Past",
               "Dragon Cultist",
               "Dungeon Delver",
               "Far Traveler",
               "Feywild Visitor",
               "Guild Artisan",
               "Hardy Outlander",
               "Inspiring Leader",
               "Street Urchin",
               "Sword Coast Sailor",
               "Veteran Soldier"}

# Useful constants related to colors
color_identities = ['', 'B', 'G', 'R', 'U', 'W', 'BG', 'BR', 'BU', 'BW',
                    'GR', 'GU', 'GW', 'RU', 'RW', 'UW', 'BGR', 'BGU', 'BGW',
                    'BRU', 'BRW', 'BUW', 'GRU', 'GRW', 'GUW', 'RUW', 'BGRU',
                    'BGRW', 'BGUW', 'BRUW', 'GRUW', 'BGRUW']

color_names = {'': 'Colorless', 'B': 'Black', 'G': 'Green', 'R': 'Red',
               'U': 'Blue', 'W': 'White',
               'BG': 'Golgari', 'BR': 'Rakdos', 'BU': 'Dimir', 'BW': 'Orzhov',
               'GR': 'Gruul', 'GU': 'Simic', 'GW': 'Selesnya', 'RU': 'Izzet',
               'RW': 'Boros', 'UW': 'Azorius',
               'BGR': 'Jund', 'BGU': 'Sultai', 'BGW': 'Abzan',
               'BRU': 'Grixis', 'BRW': 'Mardu', 'BUW': 'Esper',
               'GRU': 'Temur', 'GRW': 'Naya', 'GUW': 'Bant', 'RUW': 'Jeskai',
               'BGRU': 'Glint-Eye (No White)', 'BGRW': 'Dune-Brood (No Blue)',
               'BGUW': 'Witch-Maw (No Red)', 'BRUW': 'Yore-Tiller (No Green)',
               'GRUW': 'Ink-Treader (No Black)', 'BGRUW': '5 Color'}


def normalize_cardnames(cards: Iterable[str]) -> List[str]:
    return list(map(normalize_cardname, cards))


def normalize_cardname(cardname: str, sep="-"):
    return ''.join(char for char in cardname.lower().replace(' ', sep) 
                   if char.isalnum() or char == sep)
