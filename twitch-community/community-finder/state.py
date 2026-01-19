import json
from typing import Any

from .paths import FILTERS_PATH, CONFIG_PATH, DISCORD_CACHE_PATH

DEFAULT_FILTERS = {"min_viewers": 0, "max_viewers": None}

DEFAULT_CONFIG = {
    "PAGE_LOAD_TIMEOUT_SECONDS": 15,
    "DISCORD_WAIT_SECONDS": 8,
    "DISCORD_POLL_INTERVAL_SECONDS": 0.25,
    "PAGE_LOAD_STRATEGY": "eager",          # normal | eager | none
    "SCRAPE_WORKERS": 3,
    "SCRAPE_TIMEOUT_PER_CHANNEL": 30,
    "STREAMS_PAGE_SIZE": 100,               # Twitch max = 100

    # New: prints what Selenium/Twitch/Discord steps are doing
    "VERBOSE": False,

    # New: if True, cache empty results too (useful for debugging)
    "CACHE_EMPTY_RESULTS": True,
}

DISCORD_CACHE_TTL_SECONDS = 7 * 24 * 3600
DISCORD_EMPTY_CACHE_TTL_SECONDS = 15 * 60


def _read_json_file(path: str) -> dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _write_json_file(path: str, data: dict[str, Any]) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def load_filters() -> dict[str, Any]:
    data = _read_json_file(FILTERS_PATH)
    if not data:
        return dict(DEFAULT_FILTERS)

    mv = data.get("min_viewers", DEFAULT_FILTERS["min_viewers"])
    xv = data.get("max_viewers", DEFAULT_FILTERS["max_viewers"])

    if not isinstance(mv, int) or mv < 0:
        mv = DEFAULT_FILTERS["min_viewers"]
    if xv is not None and (not isinstance(xv, int) or xv < 0):
        xv = DEFAULT_FILTERS["max_viewers"]
    if xv is not None and mv > xv:
        mv, xv = DEFAULT_FILTERS["min_viewers"], DEFAULT_FILTERS["max_viewers"]

    return {"min_viewers": mv, "max_viewers": xv}


def save_filters(filters: dict[str, Any]) -> None:
    payload = {"min_viewers": int(filters["min_viewers"]), "max_viewers": filters["max_viewers"]}
    if payload["max_viewers"] is not None:
        payload["max_viewers"] = int(payload["max_viewers"])
    _write_json_file(FILTERS_PATH, payload)


def load_config() -> dict[str, Any]:
    data = _read_json_file(CONFIG_PATH)
    cfg = dict(DEFAULT_CONFIG)
    if not data:
        return cfg

    for k in [
        "PAGE_LOAD_TIMEOUT_SECONDS",
        "DISCORD_WAIT_SECONDS",
        "SCRAPE_WORKERS",
        "SCRAPE_TIMEOUT_PER_CHANNEL",
        "STREAMS_PAGE_SIZE",
    ]:
        v = data.get(k, cfg[k])
        if isinstance(v, int) and v > 0:
            cfg[k] = v

    v = data.get("DISCORD_POLL_INTERVAL_SECONDS", cfg["DISCORD_POLL_INTERVAL_SECONDS"])
    if isinstance(v, (int, float)) and float(v) > 0:
        cfg["DISCORD_POLL_INTERVAL_SECONDS"] = float(v)

    strat = str(data.get("PAGE_LOAD_STRATEGY", cfg["PAGE_LOAD_STRATEGY"])).lower().strip()
    if strat in ("normal", "eager", "none"):
        cfg["PAGE_LOAD_STRATEGY"] = strat

    if cfg["STREAMS_PAGE_SIZE"] > 100:
        cfg["STREAMS_PAGE_SIZE"] = 100

    vb = data.get("VERBOSE", cfg["VERBOSE"])
    if isinstance(vb, bool):
        cfg["VERBOSE"] = vb

    cer = data.get("CACHE_EMPTY_RESULTS", cfg["CACHE_EMPTY_RESULTS"])
    if isinstance(cer, bool):
        cfg["CACHE_EMPTY_RESULTS"] = cer

    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    payload = {
        "PAGE_LOAD_TIMEOUT_SECONDS": int(cfg["PAGE_LOAD_TIMEOUT_SECONDS"]),
        "DISCORD_WAIT_SECONDS": int(cfg["DISCORD_WAIT_SECONDS"]),
        "DISCORD_POLL_INTERVAL_SECONDS": float(cfg["DISCORD_POLL_INTERVAL_SECONDS"]),
        "PAGE_LOAD_STRATEGY": str(cfg["PAGE_LOAD_STRATEGY"]),
        "SCRAPE_WORKERS": int(cfg["SCRAPE_WORKERS"]),
        "SCRAPE_TIMEOUT_PER_CHANNEL": int(cfg["SCRAPE_TIMEOUT_PER_CHANNEL"]),
        "STREAMS_PAGE_SIZE": int(cfg["STREAMS_PAGE_SIZE"]),
        "VERBOSE": bool(cfg.get("VERBOSE", False)),
        "CACHE_EMPTY_RESULTS": bool(cfg.get("CACHE_EMPTY_RESULTS", True)),
    }
    if payload["STREAMS_PAGE_SIZE"] > 100:
        payload["STREAMS_PAGE_SIZE"] = 100
    _write_json_file(CONFIG_PATH, payload)


def load_discord_cache() -> dict[str, Any]:
    data = _read_json_file(DISCORD_CACHE_PATH)
    return data if isinstance(data, dict) else {}


def save_discord_cache(cache: dict[str, Any]) -> None:
    if not isinstance(cache, dict):
        return
    _write_json_file(DISCORD_CACHE_PATH, cache)
