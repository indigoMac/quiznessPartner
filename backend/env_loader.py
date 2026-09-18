"""Load environment files from the usual project locations.

`load_dotenv()` only looks in the current working directory, so running from
`backend/` would miss a repo-root `.env` and running from the root would miss
`backend/.env`. Load both; the backend file wins when both define a key.
"""

from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent


def load_app_env() -> None:
    load_dotenv(BACKEND_DIR / ".env")
    load_dotenv(ROOT_DIR / ".env")
