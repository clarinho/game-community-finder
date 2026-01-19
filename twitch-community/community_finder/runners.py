from typing import Any

from .state import load_filters, load_config
from .ui import main_menu, clear_screen, show_filters_line, show_config_line
from .formatters import bold, gray, dim, yellow, print_page_header, print_results_table
from .twitch_api import (
    get_app_token,
    get_game_id,
    get_streams_page,
    get_users_by_login,
    get_streams_by_user_ids,
    GAME_NAME,
    LANGUAGE,
)
from .discord import scrape_discord_for_logins_parallel

from.oauth_device import get_valid_user_access_token
from .twitch_api import get_followed_channels, get_users_by_ids

OUTPUT_BATCH_SIZE = 10


def passes_viewer_filters(viewers: int, f: dict[str, Any]) -> bool:
    if viewers < int(f["min_viewers"]):
        return False
    maxv = f["max_viewers"]
    if maxv is not None and viewers > int(maxv):
        return False
    return True


def sort_streams(streams: list[dict[str, Any]], sort_order: str) -> list[dict[str, Any]]:
    rev = (sort_order == "desc")
    return sorted(streams, key=lambda s: int(s.get("viewer_count", 0)), reverse=rev)


class App:
    def __init__(self) -> None:
        self.filters = load_filters()
        self.cfg = load_config()
        self.token = get_app_token()

    def run(self) -> None:
        while True:
            plan = main_menu(self.filters, self.cfg)
            if plan is None:
                return

            clear_screen()
            print(bold("=== Running ==="))
            print(gray(f"Game: {GAME_NAME} | Language: {LANGUAGE or 'any'}"))
            print(gray(show_filters_line(self.filters)))
            print(gray(show_config_line(self.cfg)))
            print()

            mode = plan["mode"]
            sort_order = plan["sort"]
            f = plan["filters"]

            if mode == "infinite":
                self.run_infinite(sort_order, f)
            elif mode == "count":
                self.run_count(int(plan["n"]), sort_order, f)
            elif mode == "names":
                self.run_names(list(plan["names"]), sort_order, f)
            elif mode == "followed":
                self.run_followed(plan["username"], sort_order, f)

            print()
            input(dim("Press Enter to return to the menu..."))

    def run_infinite(self, sort_order: str, f: dict[str, Any]) -> None:
        game_id = get_game_id(self.token, GAME_NAME)
        after: str | None = None
        page_num = 1

        print(bold("Infinite discovery started."))
        print(gray("Press Ctrl+C to stop.\n"))

        try:
            while True:
                page = get_streams_page(
                    self.token,
                    game_id,
                    LANGUAGE,
                    int(self.cfg["STREAMS_PAGE_SIZE"]),
                    after
                )
                data = page.get("data", [])
                if not data:
                    print(gray("No more streams returned. Stopping."))
                    break

                filtered = [s for s in data if passes_viewer_filters(int(s["viewer_count"]), f)]
                filtered = sort_streams(filtered, sort_order)

                idx = 0
                while idx < len(filtered):
                    chunk = filtered[idx: idx + OUTPUT_BATCH_SIZE]
                    idx += OUTPUT_BATCH_SIZE

                    logins = [s["user_login"] for s in chunk]
                    discord_map = scrape_discord_for_logins_parallel(self.cfg, logins)

                    rows: list[dict[str, Any]] = []
                    for s in chunk:
                        rows.append({
                            "name": s["user_name"],
                            "status": "LIVE",
                            "viewers": int(s["viewer_count"]),
                            "discords": discord_map.get(s["user_login"], []),
                        })

                    print_page_header(page_num)
                    print_results_table(rows)
                    page_num += 1

                pagination = page.get("pagination", {}) or {}
                after = pagination.get("cursor")
                if not after:
                    print(gray("Reached end of pagination. Stopping."))
                    break

        except KeyboardInterrupt:
            print("\n" + yellow("Stopped by user (Ctrl+C)."))

    def run_count(self, n: int, sort_order: str, f: dict[str, Any]) -> None:
        game_id = get_game_id(self.token, GAME_NAME)

        collected: list[dict[str, Any]] = []
        after: str | None = None

        while len(collected) < n:
            page = get_streams_page(
                self.token,
                game_id,
                LANGUAGE,
                int(self.cfg["STREAMS_PAGE_SIZE"]),
                after
            )

            data = page.get("data", [])
            if not data:
                break

            for s in data:
                if passes_viewer_filters(int(s["viewer_count"]), f):
                    collected.append(s)
                    if len(collected) >= n:
                        break

            pagination = page.get("pagination", {}) or {}
            after = pagination.get("cursor")
            if not after:
                break

        if not collected:
            print(gray("No matching streams found."))
            return

        collected = sort_streams(collected, sort_order)
        result = collected[:n]

        page_num = 1
        idx = 0
        while idx < len(result):
            chunk = result[idx: idx + OUTPUT_BATCH_SIZE]
            idx += OUTPUT_BATCH_SIZE

            logins = [s["user_login"] for s in chunk]
            discord_map = scrape_discord_for_logins_parallel(self.cfg, logins)

            rows: list[dict[str, Any]] = []
            for s in chunk:
                rows.append({
                    "name": s["user_name"],
                    "status": "LIVE",
                    "viewers": int(s["viewer_count"]),
                    "discords": discord_map.get(s["user_login"], []),
                })

            print_page_header(page_num)
            print_results_table(rows)
            page_num += 1

        if len(result) < n:
            print(yellow(f"Only {len(result)} matched your filters (requested {n})."))

    def run_names(self, names: list[str], sort_order: str, f: dict[str, Any]) -> None:
        users = get_users_by_login(self.token, names)
        login_to_user = {u["login"].lower(): u for u in users}

        missing = [n for n in names if n.lower() not in login_to_user]
        if missing:
            print(yellow("Not found (check spelling / login): " + ", ".join(missing)))
            print()

        if not users:
            print(gray("No valid users to check."))
            return

        user_ids = [u["id"] for u in users]
        live_streams = get_streams_by_user_ids(self.token, user_ids)
        live_by_user_id = {s["user_id"]: s for s in live_streams}

        ordered_users: list[dict[str, Any]] = []
        for n in names:
            u = login_to_user.get(n.lower())
            if u:
                ordered_users.append(u)

        live_list: list[dict[str, Any]] = []
        offline_list: list[dict[str, Any]] = []

        for u in ordered_users:
            uid = u["id"]
            s = live_by_user_id.get(uid)
            if s:
                if LANGUAGE and s.get("language") != LANGUAGE:
                    offline_list.append(u)
                    continue
                viewers = int(s.get("viewer_count", 0))
                if passes_viewer_filters(viewers, f):
                    live_list.append(s)
                else:
                    # Keep your preferred behavior for name search.
                    offline_list.append(u)
            else:
                offline_list.append(u)

        live_list = sort_streams(live_list, sort_order)

        live_logins = [s["user_login"] for s in live_list]
        offline_logins = [u["login"] for u in offline_list]
        all_logins = list(dict.fromkeys(live_logins + offline_logins))
        discord_map = scrape_discord_for_logins_parallel(self.cfg, all_logins)

        if live_list:
            print(bold("=== LIVE ===\n"))
            rows: list[dict[str, Any]] = []
            for s in live_list:
                rows.append({
                    "name": s["user_name"],
                    "status": "LIVE",
                    "viewers": int(s["viewer_count"]),
                    "discords": discord_map.get(s["user_login"], []),
                })
            print_results_table(rows)

        if offline_list:
            print(bold("=== OFFLINE (Discord still checked) ===\n"))
            rows2: list[dict[str, Any]] = []
            for u in offline_list:
                login = u["login"]
                name = u.get("display_name") or u.get("login") or login
                rows2.append({
                    "name": name,
                    "status": "OFFLINE",
                    "viewers": None,
                    "discords": discord_map.get(login, []),
                })
            print_results_table(rows2)

        if not live_list and not offline_list:
            print(gray("No results."))
    
    def run_followed(self, typed_username: str, sort_order: str, f: dict[str, Any]) -> None:
        verbose = bool(self.cfg.get("VERBOSE", False))

        # 1) user token (device flow) with required scope
        user_token = get_valid_user_access_token(["user:read:follows"], verbose=verbose)

        # 2) resolve typed username -> user_id
        users = get_users_by_login(self.token, [typed_username])
        if not users:
            print(gray("User not found."))
            return
        target = users[0]
        target_id = target["id"]

        if verbose:
            print(f"[VERBOSE] Fetching followed channels for {typed_username} (id={target_id})")

        # 3) list followed channels (pagination)
        followed = get_followed_channels(user_token, target_id, first=100)
        if not followed:
            print(gray("No followed channels returned (or not authorized)."))
            return

        # followed items include broadcaster_id and broadcaster_name
        broadcaster_ids = [x["broadcaster_id"] for x in followed if x.get("broadcaster_id")]
        # 4) live status + viewers
        live_streams = get_streams_by_user_ids(self.token, broadcaster_ids)
        live_by_id = {s["user_id"]: s for s in live_streams}

        # 5) fetch user logins/display for offline too
        users2 = get_users_by_ids(self.token, broadcaster_ids)
        id_to_user = {u["id"]: u for u in users2}

        # build rows
        rows: list[dict[str, Any]] = []
        for bid in broadcaster_ids:
            u = id_to_user.get(bid, {})
            login = u.get("login") or ""
            name = u.get("display_name") or u.get("login") or bid

            s = live_by_id.get(bid)
            if s:
                viewers = int(s.get("viewer_count", 0))
                status = "LIVE"
            else:
                viewers = None
                status = "OFFLINE"

            rows.append({"name": name, "login": login, "status": status, "viewers": viewers})

        # sort
        if sort_order == "asc":
            rows.sort(key=lambda r: (r["viewers"] is None, r["viewers"] or 0))
        else:
            rows.sort(key=lambda r: (r["viewers"] is None, -(r["viewers"] or 0)))

        # 6) discord scrape (cached) and print pages
        page_num = 1
        idx = 0
        while idx < len(rows):
            chunk = rows[idx: idx + OUTPUT_BATCH_SIZE]
            idx += OUTPUT_BATCH_SIZE

            logins = [r["login"] for r in chunk if r.get("login")]
            discord_map = scrape_discord_for_logins_parallel(self.cfg, logins)

            out_rows: list[dict[str, Any]] = []
            for r in chunk:
                out_rows.append({
                    "name": r["name"],
                    "status": r["status"],
                    "viewers": r["viewers"],
                    "discords": discord_map.get(r["login"], []),
                })

            print_page_header(page_num)
            print_results_table(out_rows)
            page_num += 1

