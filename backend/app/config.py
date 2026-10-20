import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)


def require_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"{name} is not set in the environment variables. Add it to the .env file in the repo root.")

    return value


GEMINI_API_KEY = require_env("GEMINI_API_KEY")

GEMINI_MODEL_NAME = require_env("MODEL_NAME")

VERIFIER_MODEL_NAME = require_env("VERIFIER_MODEL_NAME")
