"""
Статический справочник: валюта → названия стран на 5 языках.

Языки: en, ru, es, fr, de (английский, русский, испанский, французский, немецкий).
Для EUR перечислены все основные страны еврозоны — у них одна валюта.
"""

from __future__ import annotations

from typing import TypedDict


class CurrencyCountries(TypedDict):
    currency: str
    names: dict[str, list[str]]


# --- Еврозона и прочие страны с EUR ---
_EUR_EN = [
    "Germany", "Malta", "France", "Italy", "Spain", "Netherlands", "Belgium",
    "Austria", "Portugal", "Greece", "Ireland", "Finland", "Luxembourg", "Cyprus",
    "Estonia", "Latvia", "Lithuania", "Slovakia", "Slovenia", "Croatia",
    "Andorra", "Monaco", "San Marino", "Vatican", "Vatican City", "Montenegro",
    "Kosovo", "Europe", "Eurozone", "European Union", "EU",
]
_EUR_RU = [
    "германия", "мальта", "франция", "италия", "испания", "голландия", "нидерланды",
    "бельгия", "австрия", "португалия", "греция", "ирландия", "финляндия",
    "люксембург", "кипр", "эстония", "латвия", "литва", "словакия", "словения",
    "хорватия", "андорра", "монако", "сан-марино", "ватикан", "черногория",
    "косово", "европа", "еврозона", "ес", "европейский союз",
]
_EUR_ES = [
    "alemania", "malta", "francia", "italia", "españa", "espana", "holanda",
    "paises bajos", "belgica", "austria", "portugal", "grecia", "irlanda",
    "finlandia", "luxemburgo", "chipre", "estonia", "letonia", "lituania",
    "eslovaquia", "eslovenia", "croacia", "andorra", "monaco", "san marino",
    "vaticano", "montenegro", "kosovo", "europa", "eurozona", "union europea",
]
_EUR_FR = [
    "allemagne", "malte", "france", "italie", "espagne", "pays-bas", "belgique",
    "autriche", "portugal", "grece", "irlande", "finlande", "luxembourg", "chypre",
    "estonie", "lettonie", "lituanie", "slovaquie", "slovenie", "croatie",
    "andorre", "monaco", "saint-marin", "vatican", "montenegro", "kosovo",
    "europe", "zone euro", "union europeenne",
]
_EUR_DE = [
    "deutschland", "malta", "frankreich", "italien", "spanien", "niederlande",
    "holland", "belgien", "osterreich", "österreich", "portugal", "griechenland",
    "irland", "finnland", "luxemburg", "zypern", "estland", "lettland", "litauen",
    "slowakei", "slowenien", "kroatien", "andorra", "monaco", "san marino",
    "vatikan", "montenegro", "kosovo", "europa", "eurozone", "europaische union",
]

COUNTRY_ENTRIES: list[CurrencyCountries] = [
    {
        "currency": "EUR",
        "names": {
            "en": _EUR_EN,
            "ru": _EUR_RU,
            "es": _EUR_ES,
            "fr": _EUR_FR,
            "de": _EUR_DE,
        },
    },
    {
        "currency": "RUB",
        "names": {
            "en": ["Russia", "Russian Federation"],
            "ru": ["россия", "рф", "российская федерация"],
            "es": ["rusia", "federacion rusa"],
            "fr": ["russie", "federation de russie"],
            "de": ["russland", "russische foderation"],
        },
    },
    {
        "currency": "USD",
        "names": {
            "en": ["United States", "USA", "US", "America", "United States of America"],
            "ru": ["сша", "америка", "соединенные штаты", "штаты"],
            "es": ["estados unidos", "eeuu", "america"],
            "fr": ["etats-unis", "etats unis", "amerique"],
            "de": ["vereinigte staaten", "usa", "amerika"],
        },
    },
    {
        "currency": "GBP",
        "names": {
            "en": ["United Kingdom", "UK", "Britain", "Great Britain", "England"],
            "ru": ["великобритания", "англия", "британия", "соединенное королевство"],
            "es": ["reino unido", "gran bretana", "inglaterra"],
            "fr": ["royaume-uni", "grande-bretagne", "angleterre"],
            "de": ["vereinigtes konigreich", "grossbritannien", "england"],
        },
    },
    {
        "currency": "CNY",
        "names": {
            "en": ["China", "PRC", "People's Republic of China"],
            "ru": ["китай", "кнр", "китайская народная республика"],
            "es": ["china", "republica popular china"],
            "fr": ["chine", "republique populaire de chine"],
            "de": ["china", "volksrepublik china"],
        },
    },
    {
        "currency": "JPY",
        "names": {
            "en": ["Japan"],
            "ru": ["япония", "тайланд"],  # опечатка тайланд часто путают — уберу тайланд отсюда
            "es": ["japon"],
            "fr": ["japon"],
            "de": ["japan"],
        },
    },
    {
        "currency": "THB",
        "names": {
            "en": ["Thailand"],
            "ru": ["таиланд", "тайланд", "тайландия"],
            "es": ["tailandia", "tailandia"],
            "fr": ["thailande", "thailande"],
            "de": ["thailand"],
        },
    },
    {
        "currency": "TRY",
        "names": {
            "en": ["Turkey", "Türkiye", "Turkiye"],
            "ru": ["турция", "турцияя"],
            "es": ["turquia"],
            "fr": ["turquie"],
            "de": ["turkei", "türkei"],
        },
    },
    {
        "currency": "CHF",
        "names": {
            "en": ["Switzerland"],
            "ru": ["швейцария"],
            "es": ["suiza"],
            "fr": ["suisse"],
            "de": ["schweiz"],
        },
    },
    {
        "currency": "PLN",
        "names": {
            "en": ["Poland"],
            "ru": ["польша"],
            "es": ["polonia"],
            "fr": ["pologne"],
            "de": ["polen"],
        },
    },
    {
        "currency": "CZK",
        "names": {
            "en": ["Czech Republic", "Czechia"],
            "ru": ["чехия", "чешская республика"],
            "es": ["republica checa", "chequia"],
            "fr": ["republique tcheque", "tchequie"],
            "de": ["tschechien", "tschechische republik"],
        },
    },
    {
        "currency": "HUF",
        "names": {
            "en": ["Hungary"],
            "ru": ["венгрия"],
            "es": ["hungria"],
            "fr": ["hongrie"],
            "de": ["ungarn"],
        },
    },
    {
        "currency": "RON",
        "names": {
            "en": ["Romania"],
            "ru": ["румыния", "ромыния"],
            "es": ["rumania"],
            "fr": ["roumanie"],
            "de": ["rumanien"],
        },
    },
    {
        "currency": "BGN",
        "names": {
            "en": ["Bulgaria"],
            "ru": ["болгария"],
            "es": ["bulgaria"],
            "fr": ["bulgarie"],
            "de": ["bulgarien"],
        },
    },
    {
        "currency": "SEK",
        "names": {
            "en": ["Sweden"],
            "ru": ["швеция"],
            "es": ["suecia"],
            "fr": ["suede"],
            "de": ["schweden"],
        },
    },
    {
        "currency": "NOK",
        "names": {
            "en": ["Norway"],
            "ru": ["норвегия"],
            "es": ["noruega"],
            "fr": ["norvege"],
            "de": ["norwegen"],
        },
    },
    {
        "currency": "DKK",
        "names": {
            "en": ["Denmark"],
            "ru": ["дания"],
            "es": ["dinamarca"],
            "fr": ["danemark"],
            "de": ["danemark"],
        },
    },
    {
        "currency": "ISK",
        "names": {
            "en": ["Iceland"],
            "ru": ["исландия"],
            "es": ["islandia"],
            "fr": ["islande"],
            "de": ["island"],
        },
    },
    {
        "currency": "UAH",
        "names": {
            "en": ["Ukraine"],
            "ru": ["украина"],
            "es": ["ucrania"],
            "fr": ["ukraine"],
            "de": ["ukraine"],
        },
    },
    {
        "currency": "BYN",
        "names": {
            "en": ["Belarus"],
            "ru": ["беларусь", "белоруссия"],
            "es": ["bielorrusia"],
            "fr": ["bielorussie"],
            "de": ["weissrussland", "belarus"],
        },
    },
    {
        "currency": "KZT",
        "names": {
            "en": ["Kazakhstan"],
            "ru": ["казахстан"],
            "es": ["kazajistan"],
            "fr": ["kazakhstan"],
            "de": ["kasachstan"],
        },
    },
    {
        "currency": "GEL",
        "names": {
            "en": ["Georgia"],
            "ru": ["грузия"],
            "es": ["georgia"],
            "fr": ["georgie"],
            "de": ["georgien"],
        },
    },
    {
        "currency": "AMD",
        "names": {
            "en": ["Armenia"],
            "ru": ["армения"],
            "es": ["armenia"],
            "fr": ["armenie"],
            "de": ["armenien"],
        },
    },
    {
        "currency": "AZN",
        "names": {
            "en": ["Azerbaijan"],
            "ru": ["азербайджан"],
            "es": ["azerbaiyan"],
            "fr": ["azerbaidjan"],
            "de": ["aserbaidschan"],
        },
    },
    {
        "currency": "AED",
        "names": {
            "en": ["United Arab Emirates", "UAE", "Emirates", "Dubai"],
            "ru": ["оаэ", "эмираты", "дубай", "объединенные арабские эмираты"],
            "es": ["emiratos arabes unidos", "emiratos", "dubai"],
            "fr": ["emirats arabes unis", "emirats", "dubai"],
            "de": ["vereinigte arabische emirate", "vae", "dubai"],
        },
    },
    {
        "currency": "SAR",
        "names": {
            "en": ["Saudi Arabia"],
            "ru": ["саудовская аравия"],
            "es": ["arabia saudita"],
            "fr": ["arabie saoudite"],
            "de": ["saudi-arabien"],
        },
    },
    {
        "currency": "ILS",
        "names": {
            "en": ["Israel"],
            "ru": ["израиль"],
            "es": ["israel"],
            "fr": ["israel"],
            "de": ["israel"],
        },
    },
    {
        "currency": "EGP",
        "names": {
            "en": ["Egypt"],
            "ru": ["египет"],
            "es": ["egipto"],
            "fr": ["egypte"],
            "de": ["agypten", "ägypten"],
        },
    },
    {
        "currency": "INR",
        "names": {
            "en": ["India"],
            "ru": ["индия"],
            "es": ["india"],
            "fr": ["inde"],
            "de": ["indien"],
        },
    },
    {
        "currency": "KRW",
        "names": {
            "en": ["South Korea", "Korea", "Republic of Korea"],
            "ru": ["корея", "южная корея"],
            "es": ["corea del sur", "corea"],
            "fr": ["coree du sud", "coree"],
            "de": ["sudkorea", "korea"],
        },
    },
    {
        "currency": "VND",
        "names": {
            "en": ["Vietnam", "Viet Nam"],
            "ru": ["вьетнам"],
            "es": ["vietnam"],
            "fr": ["vietnam"],
            "de": ["vietnam"],
        },
    },
    {
        "currency": "IDR",
        "names": {
            "en": ["Indonesia"],
            "ru": ["индонезия"],
            "es": ["indonesia"],
            "fr": ["indonesie"],
            "de": ["indonesien"],
        },
    },
    {
        "currency": "MYR",
        "names": {
            "en": ["Malaysia"],
            "ru": ["малайзия"],
            "es": ["malasia"],
            "fr": ["malaisie"],
            "de": ["malaysia"],
        },
    },
    {
        "currency": "SGD",
        "names": {
            "en": ["Singapore"],
            "ru": ["сингапур"],
            "es": ["singapur"],
            "fr": ["singapour"],
            "de": ["singapur"],
        },
    },
    {
        "currency": "PHP",
        "names": {
            "en": ["Philippines"],
            "ru": ["филиппины"],
            "es": ["filipinas"],
            "fr": ["philippines"],
            "de": ["philippinen"],
        },
    },
    {
        "currency": "HKD",
        "names": {
            "en": ["Hong Kong"],
            "ru": ["гонконг", "гон конг"],
            "es": ["hong kong"],
            "fr": ["hong kong"],
            "de": ["hongkong"],
        },
    },
    {
        "currency": "AUD",
        "names": {
            "en": ["Australia"],
            "ru": ["австралия"],
            "es": ["australia"],
            "fr": ["australie"],
            "de": ["australien"],
        },
    },
    {
        "currency": "NZD",
        "names": {
            "en": ["New Zealand"],
            "ru": ["новая зеландия", "новая зеландия"],
            "es": ["nueva zelanda"],
            "fr": ["nouvelle-zelande"],
            "de": ["neuseeland"],
        },
    },
    {
        "currency": "CAD",
        "names": {
            "en": ["Canada"],
            "ru": ["канада"],
            "es": ["canada"],
            "fr": ["canada"],
            "de": ["kanada"],
        },
    },
    {
        "currency": "MXN",
        "names": {
            "en": ["Mexico"],
            "ru": ["мексика"],
            "es": ["mexico"],
            "fr": ["mexique"],
            "de": ["mexiko"],
        },
    },
    {
        "currency": "BRL",
        "names": {
            "en": ["Brazil"],
            "ru": ["бразилия"],
            "es": ["brasil"],
            "fr": ["bresil"],
            "de": ["brasilien"],
        },
    },
    {
        "currency": "ARS",
        "names": {
            "en": ["Argentina"],
            "ru": ["аргентина"],
            "es": ["argentina"],
            "fr": ["argentine"],
            "de": ["argentinien"],
        },
    },
    {
        "currency": "ZAR",
        "names": {
            "en": ["South Africa"],
            "ru": ["юар", "южная африка"],
            "es": ["sudafrica"],
            "fr": ["afrique du sud"],
            "de": ["sudafrika"],
        },
    },
    {
        "currency": "MAD",
        "names": {
            "en": ["Morocco"],
            "ru": ["марокко"],
            "es": ["marruecos"],
            "fr": ["maroc"],
            "de": ["marokko"],
        },
    },
    {
        "currency": "TND",
        "names": {
            "en": ["Tunisia"],
            "ru": ["тунис"],
            "es": ["tunez"],
            "fr": ["tunisie"],
            "de": ["Tunesien", "tunesien"],
        },
    },
    {
        "currency": "RSD",
        "names": {
            "en": ["Serbia"],
            "ru": ["сербия"],
            "es": ["serbia"],
            "fr": ["serbie"],
            "de": ["serbien"],
        },
    },
    {
        "currency": "MKD",
        "names": {
            "en": ["North Macedonia", "Macedonia"],
            "ru": ["македония", "северная македония"],
            "es": ["macedonia del norte"],
            "fr": ["macedoine du nord"],
            "de": ["nordmazedonien"],
        },
    },
    {
        "currency": "ALL",
        "names": {
            "en": ["Albania"],
            "ru": ["албания"],
            "es": ["albania"],
            "fr": ["albanie"],
            "de": ["albanien"],
        },
    },
    {
        "currency": "BAM",
        "names": {
            "en": ["Bosnia and Herzegovina", "Bosnia"],
            "ru": ["босния", "босния и герцеговина"],
            "es": ["bosnia"],
            "fr": ["bosnie"],
            "de": ["bosnien"],
        },
    },
]

# Исправление: убрать ошибочную привязку «тайланд» к JPY в ru
for entry in COUNTRY_ENTRIES:
    if entry["currency"] == "JPY":
        entry["names"]["ru"] = [n for n in entry["names"]["ru"] if n != "тайланд"]
