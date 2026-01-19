import json
import os
from typing import Any

# secrets.json lives in the project root (same folder as main.py)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_PATH = os.path.join(PROJECT_DIR, "secrets.json")


class SettingsError(RuntimeError):
    pass


def _read_json(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise SettingsError("secrets.json must contain a JSON object.")
        return data
    except FileNotFoundError:
        raise SettingsError(f"Missing secrets file: {path}")
    except json.JSONDecodeError as e:
        raise SettingsError(f"Invalid JSON in secrets.json: {e}")
    except OSError as e:
        raise SettingsError(f"Failed to read secrets.json: {e}")


def load_settings() -> dict[str, str]:
    data = _read_json(SECRETS_PATH)

    def req(key: str) -> str:
        v = data.get(key)
        if not isinstance(v, str) or not v.strip():
            raise SettingsError(f"Missing or empty key in secrets.json: {key}")
        return v.strip()

    settings = {
        "TWITCH_CLIENT_ID": req("TWITCH_CLIENT_ID"),
        "TWITCH_CLIENT_SECRET": req("TWITCH_CLIENT_SECRET"),
        "CHROME_BINARY_PATH": req("CHROME_BINARY_PATH"),
        "CHROMEDRIVER_PATH": req("CHROMEDRIVER_PATH"),
    }
    return settings
