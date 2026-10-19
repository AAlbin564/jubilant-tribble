# SMHI Constants
MAX_DATA_AGE_DAYS = 3

MAX_STATION_ATTEMPTS = 4

MIN_DAYS_WITH_DATA = 12

SMHI_BASE_URL = "https://opendata-download-metobs.smhi.se/api/version/1.0"

SMHI_API_URL = SMHI_BASE_URL + "/parameter/{param}/station/{station_id}/period/latest-months/data.json"


MUSHROOM_ARTICLE_TITLES = ["Cantharellus_cibarius", "Craterellus_tubaeformis", "Craterellus_cornucopioides", "Amanita_virosa", "Amanita_phalloides", "Boletus_edulis", "Tylopilus_felleus", "Cortinarius_rubellus", "Cortinarius_armillatus", "Macrolepiota_procera"]

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

WIKIPEDIA_HEADERS = {"User-Agent": "mushroom-assistant/0.1 (https://github.com/AAlbin564/jubilant-tribble)"}

EXCLUDED_ARTICLE_SECTIONS = ["taxonomy", "etymology", "research", "references", "see also", "external links", "notes", "gallery", "culture", "biochemistry", "cultivation", "non-native introductions", "pests and predators", "commercial harvest", "oncology", "notable victims", "related species", "potential uses", "sources", "common names"]