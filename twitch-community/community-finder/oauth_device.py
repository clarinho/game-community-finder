import json
import os
import time
from typing import Any

import requests

from .settings import load_settings

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_TOKEN_PATH = os.path.join(PROJECT_DIR, "user_token.json")

DEVICE_ENDPOINT = "https://id.twitch.tv/oauth2/device"
TOKEN_ENDPOINT = "https://id.twitch.tv/oauth2/token"


class OAuthError(RuntimeError):
    pass


def _write_json(path: str, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _read_json(path: str) -> dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def load_user_token() -> dict[str, Any] | None:
    return _read_json(USER_TOKEN_PATH)


def save_user_token(token_data: dict[str, Any]) -> None:
    _write_json(USER_TOKEN_PATH, token_data)


def device_authorize(scopes: list[str], verbose: bool = False) -> dict[str, Any]:
    """
    Starts Device Code Flow. Returns dict containing:
      device_code, user_code, verification_uri, expires_in, interval
    """
    s = load_settings()
    payload = {
        "client_id": s["TWITCH_CLIENT_ID"],
        "scopes": " ".join(scopes),
    }
    if verbose:
        print(f"[VERBOSE] Requesting device code for scopes: {payload['scopes']}")

    r = requests.post(DEVICE_ENDPOINT, data=payload, timeout=20)
    r.raise_for_status()
    return r.json()


def device_poll_token(device_code: str, interval: int, verbose: bool = False) -> dict[str, Any]:
    """
    Polls token endpoint until authorized or expired.
    Uses correct grant_type: urn:ietf:params:oauth:grant-type:device_code
    """
    s = load_settings()

    while True:
        data = {
            "client_id": s["TWITCH_CLIENT_ID"],
            "client_secret": s["TWITCH_CLIENT_SECRET"],
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }

        r = requests.post(TOKEN_ENDPOINT, data=data, timeout=20)

        if r.status_code == 200:
            token = r.json()
            if verbose:
                print("[VERBOSE] Device code authorized. Token received.")
            return token

        # Twitch returns JSON errors like authorization_pending, slow_down, expired_token, access_denied
        try:
            err = r.json()
        except Exception:
            raise OAuthError(f"Token polling failed: HTTP {r.status_code} {r.text}")

        msg = err.get("message") or err.get("error_description") or str(err)

        # Twitch can put the error in different fields depending on endpoint/version
        # Examples:
        #   {"error":"authorization_pending", ...}
        #   {"status":400,"message":"authorization_pending"}
        #   {"message":"authorization_pending"}
        err_code = (err.get("error") or err.get("message") or "").strip().lower()

        if verbose:
            status = err.get("status", r.status_code)
            print(f"[VERBOSE] Poll: {status} {err_code or msg}")

        if err_code == "authorization_pending":
            time.sleep(interval)
            continue

        if err_code == "slow_down":
            interval = interval + 2
            time.sleep(interval)
            continue

        if err_code in ("expired_token", "access_denied", "invalid_device_code"):
            raise OAuthError(f"Device flow failed: {err_code} {msg}")

        raise OAuthError(f"Device flow error: {err}")



def refresh_user_token(refresh_token: str, verbose: bool = False) -> dict[str, Any]:
    """
    Refresh user access token using refresh_token grant.
    """
    s = load_settings()
    data = {
        "client_id": s["TWITCH_CLIENT_ID"],
        "client_secret": s["TWITCH_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    if verbose:
        print("[VERBOSE] Refreshing user token...")

    r = requests.post(TOKEN_ENDPOINT, data=data, timeout=20)
    r.raise_for_status()
    return r.json()


def get_valid_user_access_token(scopes: list[str], verbose: bool = False) -> str:
    """
    Returns a valid user access token with required scopes.
    Stores token in user_token.json.
    """
    saved = load_user_token()

    # If we have a refresh token, try refresh first
    if saved and isinstance(saved.get("refresh_token"), str) and saved["refresh_token"]:
        try:
            newtok = refresh_user_token(saved["refresh_token"], verbose=verbose)
            save_user_token(newtok)
            return newtok["access_token"]
        except Exception as e:
            if verbose:
                print(f"[VERBOSE] Refresh failed, falling back to device flow: {e}")

    # Start device flow
    d = device_authorize(scopes, verbose=verbose)

    print("\n=== Twitch Authorization Required ===")
    print(f"Open: {d.get('verification_uri')}")
    print(f"Enter code: {d.get('user_code')}")
    print("Approve access in the browser.\n")

    token = device_poll_token(d["device_code"], int(d.get("interval", 5)), verbose=verbose)
    save_user_token(token)
    return token["access_token"]
