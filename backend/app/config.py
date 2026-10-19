import os
from dotenv import load_dotenv


def load_gemini_key() -> str:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")

    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment variables.")

    return key

GEMINI_API_KEY = load_gemini_key()