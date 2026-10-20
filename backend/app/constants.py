import re
from pathlib import Path

# PATH constants
DATA_DIR = Path(__file__).parent.parent / "data"

KNOWLEDGE_DIR = DATA_DIR / "knowledge"

VECTOR_STORE_PATH = DATA_DIR / "vector_store.json"

# HTTP constants
HTTP_TIMEOUT_SECONDS = 10

# SMHI Constants
MAX_DATA_AGE_DAYS = 3

MAX_STATION_ATTEMPTS = 4

MIN_DAYS_WITH_DATA = 12

SMHI_RAIN_PARAMETER = "5"

SMHI_BASE_URL = "https://opendata-download-metobs.smhi.se/api/version/1.0"

SMHI_API_URL = SMHI_BASE_URL + "/parameter/{param}/station/{station_id}/period/latest-months/data.json"

# GEOCODING constants
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"

# GBIF constants
GBIF_OCCURRENCE_URL = "https://api.gbif.org/v1/occurrence/search"

GBIF_TIMEOUT_SECONDS = 15

GBIF_RESULT_LIMIT = 300

MAX_DISTANCE = 40

# WIKIPEDIA constants
MUSHROOM_ARTICLE_TITLES = ["Cantharellus_cibarius", "Craterellus_tubaeformis", "Craterellus_cornucopioides", "Amanita_virosa", "Amanita_phalloides", "Boletus_edulis", "Tylopilus_felleus", "Cortinarius_rubellus", "Cortinarius_armillatus", "Macrolepiota_procera"]

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

WIKIPEDIA_HEADERS = {"User-Agent": "mushroom-assistant/0.1 (https://github.com/AAlbin564/jubilant-tribble)"}

WIKI_SECTION_HEADER = re.compile(r"^(={2,})\s*(.*?)\s*\1\s*$", re.MULTILINE)

EXCLUDED_ARTICLE_SECTIONS = ["taxonomy", "etymology", "research", "references", "see also", "external links", "notes", "gallery", "culture", "biochemistry", "cultivation", "non-native introductions", "pests and predators", "commercial harvest", "oncology", "notable victims", "related species", "potential uses", "sources", "common names"]

# RAG constants
EMBEDDING_MODEL_NAME = "models/gemini-embedding-001"

MARKDOWN_SECTION_HEADERS = [("##", "h2"), ("###", "h3"), ("####", "h4")]

CHUNK_SIZE = 2000

CHUNK_OVERLAP = 150

SEARCH_RESULTS = 5

# GRAPH constants
LLM_TIMEOUT_SECONDS = 30

LLM_MAX_RETRIES = 1

MAX_REVISIONS = 2

MAX_TOOL_ROUNDS = 5

TOOL_LIMIT_MESSAGE = (
    "You have used all your tool calls for this question. Answer now with the information you already have. "
    "If the knowledge base does not cover something, tell the user that instead of guessing."
)

SAFETY_GUIDELINES = """
1. When a specific edible mushroom is discussed in detail, always mention its dangerous lookalikes.
2. If the user is trying to identify a mushroom, tell them to confirm with a local mushroom expert.
3. Cite the source URL for facts taken from the knowledge base.
4. Never give preparation or cooking instructions for a toxic mushroom.
5. If weather data is marked stale or incomplete, say so.
6. Species facts must be supported by knowledge base results.
7. If the draft discusses a specific mushroom species as edible, a knowledge base search for that species' poisonous lookalikes must be performed.
"""

ASSISTANT_SYSTEM_MESSAGE = """You are a helpful assistant that helps users in Sweden with knowledge about mushrooms.
Use your tools to look up facts, and write clear, well-structured answers.
The knowledge base only covers a small set of species. If a search does not return the species you need,
do not repeat it: tell the user the knowledge base does not cover that species.
A reviewer checks every draft for safety before it reaches the user, and may send it back with issues to fix."""

VERIFIER_SYSTEM_MESSAGE = f"""You are a strict safety reviewer. Your job is to find problems.
You receive the user's question, the evidence the assistant gathered with its tools, and the
assistant's draft.

Check the draft for these problems specifically:
- Wrong species: compare the species the user asked about with the species the draft gives
  facts about. Facts about a different species than the one asked about are a problem,
  even if clearly labelled.
- Unsupported claims: every factual statement in the draft (toxicity, season, habitat,
  numbers) must appear in the evidence. Safety facts from general knowledge count as
  unsupported, even if they are true.
- Missing safety warnings: for species the draft presents as edible, dangerous lookalikes
  must be mentioned. For toxic species, flag anything that reads as advice on finding or
  preparing them for eating.

The knowledge base only covers a small set of species. If the evidence shows the species was
searched for but not found, a draft that says the knowledge base does not cover it, and makes
no claims about it, is correct.

Also check the guidelines below. Do not judge style or tone.
Approve only if you find no problems. Otherwise reject, and list each problem as an issue
that says exactly what is missing or wrong, so the assistant can fix it.

Guidelines:
{SAFETY_GUIDELINES}"""

DEFAULT_REJECTION_ISSUE = "The draft does not follow the guidelines. Check it against each one."

SAFETY_NOTE = (
    "\n\n⚠️ This answer could not be fully safety-checked. Never eat a wild mushroom based on "
    "this answer alone — always confirm with a local mushroom expert."
)

# API constants
MAX_THREAD_ID_LENGTH = 64

MAX_MESSAGE_LENGTH = 2000
