# Morocco identifiers
MOROCCO_ISO2 = "MA"
MOROCCO_ISO3 = "MAR"
MOROCCO_M49 = "504"
MOROCCO_NAME_FR = "Maroc"
MOROCCO_NAME_EN = "Morocco"

# HS textile chapters (50-63)
TEXTILE_HS_CHAPTERS = [str(i) for i in range(50, 64)]
TEXTILE_HS_CHAPTERS_STR = ",".join(TEXTILE_HS_CHAPTERS)

# HS chapter descriptions (French)
HS_CHAPTER_DESCRIPTIONS_FR = {
    "50": "Soie",
    "51": "Laine, poils fins ou grossiers",
    "52": "Coton",
    "53": "Autres fibres textiles vegetales",
    "54": "Filaments synthetiques ou artificiels",
    "55": "Fibres synthetiques ou artificielles discontinues",
    "56": "Ouates, feutres et non-tisses",
    "57": "Tapis et autres revetements de sol",
    "58": "Tissus speciaux",
    "59": "Tissus impregnes, enduits ou recouverts",
    "60": "Etoffes de bonneterie",
    "61": "Vetements et accessoires en bonneterie",
    "62": "Vetements et accessoires autres qu'en bonneterie",
    "63": "Autres articles textiles confectionnes",
}

# Priority chapters (High priority in design doc)
HIGH_PRIORITY_CHAPTERS = ["52", "54", "55", "60", "61", "62"]

# Top EU trading partners for Morocco textiles (Eurostat reporter codes)
EU_TOP_PARTNERS = [
    "FR",  # France
    "ES",  # Spain
    "DE",  # Germany
    "IT",  # Italy
    "PT",  # Portugal
    "BE",  # Belgium
    "NL",  # Netherlands
    "PL",  # Poland
    "RO",  # Romania
    "CZ",  # Czech Republic
]

EU_PARTNER_NAMES_FR = {
    "FR": "France",
    "ES": "Espagne",
    "DE": "Allemagne",
    "IT": "Italie",
    "PT": "Portugal",
    "BE": "Belgique",
    "NL": "Pays-Bas",
    "PL": "Pologne",
    "RO": "Roumanie",
    "CZ": "Republique tcheque",
}

# Top global partners for Comtrade queries (M49 codes)
GLOBAL_TOP_PARTNERS_M49 = {
    "250": "France",
    "724": "Espagne",
    "276": "Allemagne",
    "380": "Italie",
    "620": "Portugal",
    "840": "Etats-Unis",
    "156": "Chine",
    "792": "Turquie",
    "699": "Inde",
    "0": "Monde",
}

# Federal Register agency slugs for textile regulations
FR_TEXTILE_AGENCIES = [
    "international-trade-administration",
    "international-trade-commission",
    "customs-and-border-protection",
    "committee-for-the-implementation-of-textile-agreements",
]

# News categories
NEWS_CATEGORIES = [
    "regulatory",
    "market",
    "policy",
    "trade_agreement",
    "industry",
    "sustainability",
    "technology",
]

# Data source names
SOURCE_EUROSTAT = "eurostat_comext"
SOURCE_COMTRADE = "un_comtrade"
SOURCE_FEDERAL_REGISTER = "federal_register"
SOURCE_GENERAL_WATCHER = "openai_search"
SOURCE_OTEXA = "otexa_tradegov"

ALL_SOURCES = [
    SOURCE_EUROSTAT,
    SOURCE_COMTRADE,
    SOURCE_FEDERAL_REGISTER,
    SOURCE_GENERAL_WATCHER,
    SOURCE_OTEXA,
]
