import os
from typing import Any

from .state import save_filters, save_config, DEFAULT_CONFIG
from .paths import FILTERS_PATH, CONFIG_PATH
from .formatters import bold, cyan, gray, red, green, yellow, dim


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def prompt_choice(prompt: str, valid: set[str], default: str | None = None) -> str:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw == "" and default is not None:
            raw = default
        if raw in valid:
            return raw
        print(red("Invalid choice.") + f" Valid: {', '.join(sorted(valid))}")


def prompt_int(prompt: str, default: int | None = None) -> int | None:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw == "":
            return default
        try:
            return int(raw)
        except ValueError:
            print(red("Enter a whole number."))


def prompt_float(prompt: str, default: float | None = None) -> float | None:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            print(red("Enter a number."))


def prompt_names(prompt: str) -> list[str]:
    raw = input(f"{prompt}: ").strip()
    if not raw:
        return []
    return [x for x in raw.split() if x]


def prompt_text(prompt: str) -> str:
    return input(f"{prompt}: ").strip()


def show_filters_line(filters: dict[str, Any]) -> str:
    mv = filters["min_viewers"]
    xv = filters["max_viewers"]
    max_part = "None" if xv is None else str(xv)
    return f"Filters: min_viewers={mv}  max_viewers={max_part}"


def show_config_line(cfg: dict[str, Any]) -> str:
    return (
        f"Config: workers={cfg['SCRAPE_WORKERS']} wait={cfg['DISCORD_WAIT_SECONDS']}s "
        f"poll={cfg['DISCORD_POLL_INTERVAL_SECONDS']}s strat={cfg['PAGE_LOAD_STRATEGY']} "
        f"helix_page={cfg['STREAMS_PAGE_SIZE']}"
    )


def sorting_menu() -> str:
    print("\n" + bold("Sort by:"))
    print(cyan("[1]") + " Viewers (high -> low)")
    print(cyan("[2]") + " Viewers (low -> high)")
    print(gray("[B] Back"))
    choice = prompt_choice("Choose", {"1", "2", "B", "b"}, default="1")
    if choice in ("B", "b"):
        return "back"
    return "desc" if choice == "1" else "asc"


def filter_config_menu(filters: dict[str, Any]) -> None:
    while True:
        clear_screen()
        print(bold("=== Filter Config ==="))
        print(gray(show_filters_line(filters)))
        print(gray(f"Filters file: {FILTERS_PATH}"))
        print("\n" + cyan("[1]") + " Set min viewers")
        print(cyan("[2]") + " Set max viewers")
        print(cyan("[3]") + " Clear filters")
        print(gray("[B] Back"))

        choice = prompt_choice("Choose", {"1", "2", "3", "B", "b"}, default="B")
        if choice in ("B", "b"):
            return

        if choice == "3":
            filters["min_viewers"] = 0
            filters["max_viewers"] = None
            save_filters(filters)
            print(green("Filters cleared and saved."))
            input(dim("Press Enter to continue..."))
            continue

        if choice == "1":
            mv = prompt_int("Enter min viewers", default=filters["min_viewers"])
            if mv is None:
                continue
            if mv < 0:
                print(red("Min viewers must be >= 0."))
                input(dim("Press Enter to continue..."))
                continue
            xv = filters["max_viewers"]
            if xv is not None and mv > xv:
                print(red("Min viewers cannot be greater than max viewers."))
                input(dim("Press Enter to continue..."))
                continue
            filters["min_viewers"] = mv
            save_filters(filters)
            print(green("Min viewers updated and saved."))
            input(dim("Press Enter to continue..."))
            continue

        if choice == "2":
            xv = prompt_int("Enter max viewers", default=filters["max_viewers"])
            if xv is None:
                continue
            if xv < 0:
                print(red("Max viewers must be >= 0."))
                input(dim("Press Enter to continue..."))
                continue
            mv = filters["min_viewers"]
            if xv < mv:
                print(red("Max viewers cannot be less than min viewers."))
                input(dim("Press Enter to continue..."))
                continue
            filters["max_viewers"] = xv
            save_filters(filters)
            print(green("Max viewers updated and saved."))
            input(dim("Press Enter to continue..."))
            continue


def performance_config_menu(cfg: dict[str, Any]) -> None:
    while True:
        clear_screen()
        print(bold("=== Performance Config ==="))
        print(gray(f"Config file: {CONFIG_PATH}"))
        print(gray(show_config_line(cfg)))
        print()

        print(cyan("[1]") + " PAGE_LOAD_TIMEOUT_SECONDS")
        print(cyan("[2]") + " DISCORD_WAIT_SECONDS")
        print(cyan("[3]") + " DISCORD_POLL_INTERVAL_SECONDS")
        print(cyan("[4]") + " PAGE_LOAD_STRATEGY")
        print(cyan("[5]") + " SCRAPE_WORKERS")
        print(cyan("[6]") + " SCRAPE_TIMEOUT_PER_CHANNEL")
        print(cyan("[7]") + " STREAMS_PAGE_SIZE")
        print(cyan("[8]") + " Reset to defaults")
        print(gray("[B] Back"))

        choice = prompt_choice("Choose", {"1", "2", "3", "4", "5", "6", "7", "8", "B", "b"}, default="B")
        if choice in ("B", "b"):
            return

        if choice == "8":
            cfg.clear()
            cfg.update(dict(DEFAULT_CONFIG))
            save_config(cfg)
            print(green("Config reset and saved."))
            input(dim("Press Enter to continue..."))
            continue

        if choice == "1":
            v = prompt_int("Enter PAGE_LOAD_TIMEOUT_SECONDS", default=cfg["PAGE_LOAD_TIMEOUT_SECONDS"])
            if v is not None and v > 0:
                cfg["PAGE_LOAD_TIMEOUT_SECONDS"] = v
                save_config(cfg)
            continue

        if choice == "2":
            v = prompt_int("Enter DISCORD_WAIT_SECONDS", default=cfg["DISCORD_WAIT_SECONDS"])
            if v is not None and v > 0:
                cfg["DISCORD_WAIT_SECONDS"] = v
                save_config(cfg)
            continue

        if choice == "3":
            v = prompt_float("Enter DISCORD_POLL_INTERVAL_SECONDS", default=cfg["DISCORD_POLL_INTERVAL_SECONDS"])
            if v is not None and v > 0:
                cfg["DISCORD_POLL_INTERVAL_SECONDS"] = float(v)
                save_config(cfg)
            continue

        if choice == "4":
            print("\n" + bold("PAGE_LOAD_STRATEGY:"))
            print(cyan("[1]") + " normal")
            print(cyan("[2]") + " eager")
            print(cyan("[3]") + " none")
            cur = str(cfg["PAGE_LOAD_STRATEGY"])
            default = "2" if cur == "eager" else ("1" if cur == "normal" else "3")
            m = prompt_choice(f"Choose (current: {cur})", {"1", "2", "3"}, default=default)
            cfg["PAGE_LOAD_STRATEGY"] = "normal" if m == "1" else ("eager" if m == "2" else "none")
            save_config(cfg)
            continue

        if choice == "5":
            v = prompt_int("Enter SCRAPE_WORKERS", default=cfg["SCRAPE_WORKERS"])
            if v is not None and v > 0:
                cfg["SCRAPE_WORKERS"] = v
                save_config(cfg)
            continue

        if choice == "6":
            v = prompt_int("Enter SCRAPE_TIMEOUT_PER_CHANNEL", default=cfg["SCRAPE_TIMEOUT_PER_CHANNEL"])
            if v is not None and v > 0:
                cfg["SCRAPE_TIMEOUT_PER_CHANNEL"] = v
                save_config(cfg)
            continue

        if choice == "7":
            v = prompt_int("Enter STREAMS_PAGE_SIZE (max 100)", default=cfg["STREAMS_PAGE_SIZE"])
            if v is not None and v > 0:
                cfg["STREAMS_PAGE_SIZE"] = min(100, v)
                save_config(cfg)
            continue


def main_menu(filters: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any] | None:
    while True:
        clear_screen()
        print(bold("=== Twitch Finder ==="))
        print(gray(show_filters_line(filters)))
        print(gray(show_config_line(cfg)))
        print()

        print(cyan("[1]") + " Infinite discovery")
        print(cyan("[2]") + " Specify number of streams")
        print(cyan("[3]") + " Search by name(s)")
        print(cyan("[4]") + " Filter Config")
        print(cyan("[5]") + " Performance Config")
        print(cyan("[6]") + " Followed channels lookup (requires Twitch login)")
        print(cyan("[7]") + " Exit")

        choice = prompt_choice("Choose", {"1", "2", "3", "4", "5", "6", "7"}, default="1")

        if choice == "7":
            return None

        if choice == "4":
            filter_config_menu(filters)
            continue

        if choice == "5":
            performance_config_menu(cfg)
            continue

        clear_screen()
        print(bold("=== Mode Selected ==="))
        print(gray(show_filters_line(filters)))
        print(gray(show_config_line(cfg)))

        if choice == "1":
            sort_order = sorting_menu()
            if sort_order == "back":
                continue
            return {"mode": "infinite", "sort": sort_order, "filters": dict(filters)}

        if choice == "2":
            n = prompt_int("Enter number of streams", default=40)
            if n is None or n <= 0:
                print(red("Number of streams must be >= 1."))
                input(dim("Press Enter to continue..."))
                continue

            sort_order = sorting_menu()
            if sort_order == "back":
                continue

            return {"mode": "count", "n": n, "sort": sort_order, "filters": dict(filters)}

        if choice == "3":
            names = prompt_names("Name(s)")
            if not names:
                print(yellow("No names entered. Returning to main menu."))
                input(dim("Press Enter to continue..."))
                continue

            sort_order = sorting_menu()
            if sort_order == "back":
                continue

            return {"mode": "names", "names": names, "sort": sort_order, "filters": dict(filters)}

        if choice == "6":
            username = prompt_text("Enter Twitch username (the account to read followed channels for)")
            if not username:
                print(yellow("No username entered. Returning to main menu."))
                input(dim("Press Enter to continue..."))
                continue

            sort_order = sorting_menu()
            if sort_order == "back":
                continue

            return {"mode": "followed", "username": username, "sort": sort_order, "filters": dict(filters)}
