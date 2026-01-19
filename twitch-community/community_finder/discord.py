import re
import time
from typing import Any

from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from .state import (
    load_discord_cache,
    save_discord_cache,
    DISCORD_CACHE_TTL_SECONDS,
    DISCORD_EMPTY_CACHE_TTL_SECONDS,
)
from .settings import load_settings


DISCORD_URL_REGEX = re.compile(
    r"""(?xi)
    \bhttps?://
    (?:
        (?:www\.)?
        discord\.gg/[A-Za-z0-9-]+
      |
        (?:www\.)?
        discord\.com/invite/[A-Za-z0-9-]+
      |
        (?:www\.)?
        discordapp\.com/invite/[A-Za-z0-9-]+
    )
    """
)

DISCORD_BARE_REGEX = re.compile(
    r"""(?xi)
    \b(?:
        discord\.gg/[A-Za-z0-9-]+
      |
        discord\.com/invite/[A-Za-z0-9-]+
      |
        discordapp\.com/invite/[A-Za-z0-9-]+
    )\b
    """
)

discord_cache: dict[str, Any] = load_discord_cache()


def _secrets() -> dict[str, str]:
    return load_settings()


def _v(cfg: dict[str, Any], msg: str) -> None:
    if cfg.get("VERBOSE", False):
        print(f"[VERBOSE] {msg}")


def make_driver(cfg: dict[str, Any]) -> webdriver.Chrome:
    s = _secrets()

    options = Options()
    options.binary_location = s["CHROME_BINARY_PATH"]
    options.page_load_strategy = str(cfg["PAGE_LOAD_STRATEGY"])

    # Default to headless to avoid opening visible windows
    options.add_argument("--headless=new")

    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--disable-notifications")
    options.add_argument("--mute-audio")

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
    }
    options.add_experimental_option("prefs", prefs)

    service = Service(s["CHROMEDRIVER_PATH"])

    # If this fails, we want to see it in verbose mode, not silently swallow it.
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(int(cfg["PAGE_LOAD_TIMEOUT_SECONDS"]))
    return driver


def _normalize_discord_url(u: str) -> str:
    u = u.strip().strip("\"'")
    if u.lower().startswith("http://") or u.lower().startswith("https://"):
        return u
    return "https://" + u


def _extract_discord_from_html(html: str) -> list[str]:
    found: set[str] = set()
    for m in DISCORD_URL_REGEX.finditer(html or ""):
        found.add(m.group(0))
    for m in DISCORD_BARE_REGEX.finditer(html or ""):
        found.add(_normalize_discord_url(m.group(0)))
    return sorted(found)


def extract_discord_links_from_about(driver: webdriver.Chrome, cfg: dict[str, Any], streamer_login: str) -> list[str]:
    url = f"https://www.twitch.tv/{streamer_login}/about"
    _v(cfg, f"Loading About page: {url}")

    try:
        driver.get(url)
    except TimeoutException:
        _v(cfg, f"Page load timeout for {streamer_login} (continuing)")
    except WebDriverException as e:
        _v(cfg, f"WebDriver error during get() for {streamer_login}: {e}")
        return []

    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    except WebDriverException:
        pass

    deadline = time.time() + int(cfg["DISCORD_WAIT_SECONDS"])
    poll = float(cfg["DISCORD_POLL_INTERVAL_SECONDS"])

    html = ""
    while time.time() < deadline:
        try:
            html = driver.page_source or ""
        except WebDriverException:
            html = ""
        lower = html.lower()
        if ("discord.gg" in lower) or ("discord.com/invite" in lower) or ("discordapp.com/invite" in lower):
            _v(cfg, f"Discord text detected in HTML for {streamer_login}")
            break
        time.sleep(poll)

    found: set[str] = set()

    # Pull from anchors
    try:
        anchors = driver.find_elements("tag name", "a")
        for a in anchors:
            href = a.get_attribute("href")
            if href and (DISCORD_URL_REGEX.search(href) or DISCORD_BARE_REGEX.search(href)):
                found.add(href)
    except WebDriverException:
        pass

    # Pull from HTML regex
    for x in _extract_discord_from_html(html):
        found.add(x)

    out = sorted(found)
    _v(cfg, f"Found {len(out)} Discord link(s) for {streamer_login}")
    return out


def cache_get(login: str) -> list[str] | None:
    entry = discord_cache.get(login.lower())
    if not isinstance(entry, dict):
        return None

    ts = entry.get("ts")
    links = entry.get("links")
    if not isinstance(ts, (int, float)) or not isinstance(links, list):
        return None

    links_clean = [x for x in links if isinstance(x, str)]
    ttl = DISCORD_EMPTY_CACHE_TTL_SECONDS if len(links_clean) == 0 else DISCORD_CACHE_TTL_SECONDS
    if (time.time() - ts) > ttl:
        return None

    return links_clean


def cache_set(cfg: dict[str, Any], login: str, links: list[str]) -> None:
    # IMPORTANT:
    # If CACHE_EMPTY_RESULTS is True, we cache empty too (helps avoid rescraping dead ends and proves cache works).
    if (not cfg.get("CACHE_EMPTY_RESULTS", True)) and len(links) == 0:
        return
    discord_cache[login.lower()] = {"ts": time.time(), "links": links}


def scrape_discord_for_logins_parallel(cfg: dict[str, Any], logins: list[str]) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    todo: list[str] = []

    for login in logins:
        cached = cache_get(login)
        if cached is not None:
            results[login] = cached
        else:
            todo.append(login)

    if not todo:
        return results

    _v(cfg, f"Discord scrape todo={len(todo)} cached={len(logins) - len(todo)} workers={cfg['SCRAPE_WORKERS']}")

    def worker(one_login: str) -> tuple[str, list[str], str | None]:
        # return (login, links, error_message)
        try:
            driver = make_driver(cfg)
        except Exception as e:
            return one_login, [], f"Driver failed to start: {e}"

        try:
            links = extract_discord_links_from_about(driver, cfg, one_login)
            return one_login, links, None
        except Exception as e:
            return one_login, [], f"Scrape failed: {e}"
        finally:
            try:
                driver.quit()
            except Exception:
                pass

    max_workers = int(cfg["SCRAPE_WORKERS"])
    per_channel_timeout = int(cfg["SCRAPE_TIMEOUT_PER_CHANNEL"])

    had_any_update = False

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(worker, login): login for login in todo}
        for fut in as_completed(futs):
            login = futs[fut]
            try:
                got_login, links, err = fut.result(timeout=per_channel_timeout)
                if err:
                    _v(cfg, f"{got_login}: {err}")
                results[got_login] = links
                cache_set(cfg, got_login, links)
                had_any_update = True
            except Exception as e:
                _v(cfg, f"{login}: future timeout/exception: {e}")
                results[login] = []
                cache_set(cfg, login, [])
                had_any_update = True

    if had_any_update:
        save_discord_cache(discord_cache)
        _v(cfg, "discord_cache.json saved")

    return results
