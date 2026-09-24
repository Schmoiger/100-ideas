"""Official Google GenAI Python SDK client initialization and resolution."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


def resolve_api_key(repo_root: Path | None = None) -> str | None:
    """Resolve GEMINI_API_KEY from environment or repository .env file."""
    if repo_root is not None:
        env_path = repo_root / ".env"
        if env_path.is_file():
            load_dotenv(dotenv_path=env_path)
    else:
        # Check standard repo root locations
        current = Path(__file__).resolve().parent.parent.parent
        env_path = current / ".env"
        if env_path.is_file():
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()

    return os.environ.get("GEMINI_API_KEY")


def is_live_genai_available(repo_root: Path | None = None) -> bool:
    """Return True if a non-empty GEMINI_API_KEY is configured."""
    key = resolve_api_key(repo_root)
    return bool(key and key.strip())


def get_genai_client(repo_root: Path | None = None) -> genai.Client:
    """Initialize and return a Google GenAI Client.

    Raises ValueError if GEMINI_API_KEY is not configured.
    """
    api_key = resolve_api_key(repo_root)
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured. Add GEMINI_API_KEY to your .env file "
            "or set it as an environment variable to execute live Gemini operations."
        )

    return genai.Client(api_key=api_key)
