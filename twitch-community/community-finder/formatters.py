from typing import Any
import re

ANSI_OK = True

def c(text: str, code: str) -> str:
    if not ANSI_OK:
        return text
    return f"\x1b[{code}m{text}\x1b[0m"

BOLD = "1"
DIM = "2"
RED = "31"
GREEN = "32"
YELLOW = "33"
CYAN = "36"
GRAY = "90"

def bold(t: str) -> str: return c(t, BOLD)
def dim(t: str) -> str: return c(t, DIM)
def red(t: str) -> str: return c(t, RED)
def green(t: str) -> str: return c(t, GREEN)
def yellow(t: str) -> str: return c(t, YELLOW)
def cyan(t: str) -> str: return c(t, CYAN)
def gray(t: str) -> str: return c(t, GRAY)

_SCHEME_RE = re.compile(r"(?i)^https?://")
_WWW_RE = re.compile(r"(?i)^www\.")
_TRAIL_PUNCT_RE = re.compile(r"""[)\].,;!'"`]+$""")

def normalize_discord_link_for_display(url: str) -> str | None:
    if not url:
        return None
    u = url.strip().strip("\"'")
    u = _TRAIL_PUNCT_RE.sub("", u)
    u = _SCHEME_RE.sub("", u)
    u = _WWW_RE.sub("", u)

    u_low = u.lower()

    if u_low.startswith("discordapp.com/invite/"):
        code = u.split("/", 3)[-1]
        return f"discord.gg/{code}" if code else None

    if u_low.startswith("discord.com/invite/"):
        code = u.split("/")[-1]
        return f"discord.gg/{code}" if code else None

    if u_low.startswith("discord.gg/"):
        code = u.split("/")[-1]
        return f"discord.gg/{code}" if code else None

    return None

def dedupe_discord_links(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in urls:
        norm = normalize_discord_link_for_display(raw)
        if not norm:
            continue
        key = norm.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(norm)
    return out

def pick_primary_discord_link(urls: list[str]) -> tuple[str | None, int]:
    clean = dedupe_discord_links(urls)
    if not clean:
        return None, 0
    gg = [u for u in clean if u.lower().startswith("discord.gg/")]
    inv = [u for u in clean if u.lower().startswith("discord.com/invite/")]
    ordered = gg + [u for u in inv if u not in gg] + [u for u in clean if u not in gg and u not in inv]
    return ordered[0], max(0, len(clean) - 1)

def color_status(status: str) -> str:
    if status == "LIVE":
        return green(status)
    if status == "OFFLINE":
        return red(status)
    return status

def color_discord_code_only(display_link: str) -> str:
    if "/" not in display_link:
        return display_link
    base, code = display_link.rsplit("/", 1)
    return f"{base}/" + cyan(code)

def print_page_header(page_num: int) -> None:
    print(bold(f"=== Page {page_num} ==="))

def print_results_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return

    name_w = max(4, max(len(r["name"]) for r in rows))
    status_w = len("OFFLINE")
    viewers_w = len("VIEWERS")

    header = f"{'NAME':<{name_w}}  {'STATUS':<{status_w}}  {'VIEWERS':>{viewers_w}}   DISCORD"
    line = "─" * max(62, len(header) + 2)

    print(header)
    print(line)

    for r in rows:
        name = r["name"]
        status = r["status"]
        viewers = r["viewers"]
        discords = r.get("discords", []) or []

        status_col = color_status(status)
        viewers_str = "-" if viewers is None else str(int(viewers))

        primary, extra = pick_primary_discord_link(discords)
        if primary is None:
            discord_str = "-"
        else:
            discord_str = color_discord_code_only(primary)
            if extra > 0:
                discord_str += " " + gray(f"(+{extra})")

        status_pad = " " * max(0, status_w - len(status))
        print(f"{name:<{name_w}}  {status_col}{status_pad}  {viewers_str:>{viewers_w}}   {discord_str}")

    print(line)
