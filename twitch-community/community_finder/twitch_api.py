from typing import Any
import requests

from .settings import load_settings

GAME_NAME = "League of Legends"
LANGUAGE = "en"


def _secrets() -> dict[str, str]:
    return load_settings()


def get_app_token() -> str:
    s = _secrets()
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": s["TWITCH_CLIENT_ID"],
            "client_secret": s["TWITCH_CLIENT_SECRET"],
            "grant_type": "client_credentials",
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def twitch_get(token, url: str, params: dict[str, Any]) -> dict[str, Any]:
    s = _secrets()

    # Accept either {"access_token": "..."} or "..."
    if isinstance(token, dict):
        token = token.get("access_token")

    if not token:
        raise ValueError("No valid access token provided to twitch_get")

    resp = requests.get(
        url,
        headers={
            "Client-Id": s["TWITCH_CLIENT_ID"],
            "Authorization": f"Bearer {token}",
        },
        params=params,
        timeout=20,
    )

    if resp.status_code >= 400:
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        raise requests.HTTPError(
            f"{resp.status_code} {resp.reason} for {resp.url} body={body}",
            response=resp,
        )

    return resp.json()

def get_game_id(token: str, game_name: str) -> str:
    data = twitch_get(token, "https://api.twitch.tv/helix/games", {"name": game_name})
    if not data.get("data"):
        raise RuntimeError(f"Game not found: {game_name}")
    return data["data"][0]["id"]


def get_streams_page(token: str, game_id: str, language: str, first: int, after: str | None) -> dict[str, Any]:
    params: dict[str, Any] = {"game_id": game_id, "first": first}
    if language:
        params["language"] = language
    if after:
        params["after"] = after
    return twitch_get(token, "https://api.twitch.tv/helix/streams", params)


def get_users_by_login(token: str, logins: list[str]) -> list[dict[str, Any]]:
    s = _secrets()
    users: list[dict[str, Any]] = []
    for i in range(0, len(logins), 100):
        chunk = logins[i : i + 100]
        params: list[tuple[str, str]] = [("login", x) for x in chunk]
        resp = requests.get(
            "https://api.twitch.tv/helix/users",
            headers={"Client-ID": s["TWITCH_CLIENT_ID"], "Authorization": f"Bearer {token}"},
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        users.extend(resp.json().get("data", []))
    return users


def get_users_by_ids(token: str, ids: list[str]) -> list[dict[str, Any]]:
    s = _secrets()
    users: list[dict[str, Any]] = []
    for i in range(0, len(ids), 100):
        chunk = ids[i : i + 100]
        params: list[tuple[str, str]] = [("id", x) for x in chunk]
        resp = requests.get(
            "https://api.twitch.tv/helix/users",
            headers={"Client-ID": s["TWITCH_CLIENT_ID"], "Authorization": f"Bearer {token}"},
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        users.extend(resp.json().get("data", []))
    return users


def get_streams_by_user_ids(token: str, user_ids: list[str]) -> list[dict[str, Any]]:
    s = _secrets()
    streams: list[dict[str, Any]] = []
    for i in range(0, len(user_ids), 100):
        chunk = user_ids[i : i + 100]
        params: list[tuple[str, str]] = [("user_id", x) for x in chunk]
        resp = requests.get(
            "https://api.twitch.tv/helix/streams",
            headers={"Client-ID": s["TWITCH_CLIENT_ID"], "Authorization": f"Bearer {token}"},
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        streams.extend(resp.json().get("data", []))
    return streams


def get_followed_channels(user_token: str, user_id: str, first: int = 100) -> list[dict[str, Any]]:
    """
    Calls GET /helix/channels/followed?user_id=... with pagination.
    Requires user token with scope user:read:follows.
    """
    out: list[dict[str, Any]] = []
    after: str | None = None

    while True:
        params: dict[str, Any] = {"user_id": user_id, "first": min(100, int(first))}
        if after:
            params["after"] = after

        data = twitch_get(user_token, "https://api.twitch.tv/helix/channels/followed", params)
        items = data.get("data", []) or []
        out.extend(items)

        pagination = data.get("pagination", {}) or {}
        after = pagination.get("cursor")
        if not after:
            break

    return out
