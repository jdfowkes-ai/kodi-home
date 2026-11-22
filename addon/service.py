"""Kodi Home background service entry point."""

import json
import os
import threading
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from resources.lib.kodihome import LocalStore


ADDON = xbmcaddon.Addon()
LOG_PREFIX = "Kodi Home"
APP_ART_CACHE_SECONDS = 6 * 60 * 60
STATUS_REFRESH_SECONDS = 5
IDENTITY_REFRESH_SECONDS = 5
HOME_WIDGET_CONTROL_IDS = range(300, 610)


def _call(target, method, default=None):
    try:
        value = getattr(target, method)()
        return value if value not in (None, "", [], 0) else default
    except Exception:
        return default


def _normalized_title(value):
    return " ".join(
        part for part in "".join(
            character.lower() if character.isalnum() else " "
            for character in str(value or "")
        ).split()
        if part
    )


def _media_types(value, tmdb_type=""):
    value = str(value or "").lower()
    tmdb_type = str(tmdb_type or "").lower()
    if value in ("movie",):
        return ("movie",)
    if value in ("tvshow", "season", "episode") or tmdb_type in ("tv", "tvshow"):
        return ("tvshow",)
    if tmdb_type == "movie":
        return ("movie",)
    return ("movie", "tvshow")


def _item_identity(item):
    tag = item.getVideoInfoTag()
    unique = _call(tag, "getUniqueIDs", {}) or {}
    if not isinstance(unique, dict):
        unique = {}
    for provider in ("imdb", "tmdb", "tvdb"):
        property_value = str(item.getProperty(provider + "_id") or "").strip()
        if property_value and not unique.get(provider):
            unique[provider] = property_value
    tmdb_type = item.getProperty("tmdb_type")
    return {
        "types": _media_types(_call(tag, "getMediaType", ""), tmdb_type),
        "db_id": int(_call(tag, "getDbId", 0) or 0),
        "ids": {
            (provider, str(value).strip().casefold())
            for provider, value in unique.items()
            if str(value or "").strip() and str(value).strip() != "0"
        },
        "title": _normalized_title(_call(tag, "getTitle", "") or item.getLabel()),
        "year": int(_call(tag, "getYear", 0) or 0),
    }


def _index_entry(index, media_type, title, year, unique):
    if isinstance(unique, dict):
        for provider, value in unique.items():
            value = str(value or "").strip().casefold()
            if value and value != "0":
                index["ids"].add((media_type, str(provider).casefold(), value))
    normalized = _normalized_title(title)
    if normalized:
        index["titles"].add((media_type, normalized, int(year or 0)))
        index["title_any"].add((media_type, normalized))


def _empty_identity_index():
    return {"ids": set(), "titles": set(), "title_any": set()}


def _build_library_index():
    library = _empty_identity_index()
    for method, result_key, media_type in (
        ("VideoLibrary.GetMovies", "movies", "movie"),
        ("VideoLibrary.GetTVShows", "tvshows", "tvshow"),
    ):
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": {
                "properties": ["title", "year", "uniqueid"],
                "limits": {"start": 0, "end": 5000},
            },
            "id": "kodihome-status",
        }
        try:
            response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
            for entry in response.get("result", {}).get(result_key, []):
                _index_entry(
                    library,
                    media_type,
                    entry.get("title"),
                    entry.get("year"),
                    entry.get("uniqueid") or {},
                )
        except Exception as exc:
            xbmc.log("%s: library status lookup failed: %s" % (LOG_PREFIX, exc), xbmc.LOGDEBUG)
    return library


def _build_watchlist_index(store):
    watchlist = _empty_identity_index()
    for entry in store.list_watchlist("all"):
        _index_entry(
            watchlist,
            entry.get("media_type"),
            entry.get("title"),
            entry.get("year"),
            (entry.get("metadata") or {}).get("uniqueid") or {},
        )
    return watchlist


def _identity_matches(identity, index):
    """Prefer stable provider IDs; do not match different releases by title alone."""
    for media_type in identity["types"]:
        matching_ids = {
            (provider, value) for provider, value in identity["ids"]
            if (media_type, provider, value) in index["ids"]
        }
        if matching_ids:
            return True
        # When the widget exposes provider IDs but the local record has no
        # corresponding ID, use only an exact title AND known release year.
        # Missing years are ambiguous (remakes and identically named shows).
        if identity["title"] and identity["year"] and (
            media_type, identity["title"], identity["year"]
        ) in index["titles"]:
            return True
    return False


def _decorate_home_widgets(library, watchlist):
    """Apply local status properties to every poster source on the Home hub."""
    if not xbmc.getCondVisibility("Window.IsActive(Home)"):
        return
    window = xbmcgui.Window(10000)
    control_ids = set(HOME_WIDGET_CONTROL_IDS)
    # Arctic Fuse registers the current Home rows in container 601. Each row
    # exposes its real dynamic widget control (commonly 5xxx) as widget_id.
    try:
        registry = window.getControl(601)
        for position in range(min(int(registry.size()), 500)):
            widget_id = str(registry.getListItem(position).getProperty("widget_id") or "").strip()
            if widget_id.isdigit():
                control_ids.add(int(widget_id))
    except Exception:
        pass
    for control_id in control_ids:
        try:
            control = window.getControl(control_id)
            size = min(int(control.size()), 500)
        except Exception:
            continue
        for position in range(size):
            try:
                item = control.getListItem(position)
                identity = _item_identity(item)
                in_library = _identity_matches(identity, library)
                in_watchlist = _identity_matches(identity, watchlist)
                for key, present in (("KodiHome.InLibrary", in_library), ("KodiHome.InWatchlist", in_watchlist)):
                    desired = "true" if present else "false"
                    if item.getProperty(key) != desired:
                        item.setProperty(key, desired)
            except Exception:
                continue


def _refresh_app_artwork_cache():
    # Let the home screen finish loading before gathering artwork in the background.
    time.sleep(60)
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
    cache_path = os.path.join(profile, "app-library-fanart-cache.json")
    try:
        if os.path.isfile(cache_path) and time.time() - os.path.getmtime(cache_path) < APP_ART_CACHE_SECONDS:
            return
    except Exception:
        pass

    candidates = []
    for method, result_key in (
        ("VideoLibrary.GetMovies", "movies"),
        ("VideoLibrary.GetTVShows", "tvshows"),
    ):
        try:
            request = {
                "jsonrpc": "2.0",
                "method": method,
                "params": {
                    "properties": ["art", "studio"],
                    "limits": {"start": 0, "end": 1000},
                    "sort": {"method": "title", "order": "ascending"},
                },
                "id": 1,
            }
            response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
            candidates.extend(response.get("result", {}).get(result_key, []))
        except Exception as exc:
            xbmc.log("%s: background artwork lookup failed for %s: %s" % (LOG_PREFIX, method, exc), xbmc.LOGDEBUG)

    try:
        os.makedirs(profile, exist_ok=True)
        temporary_path = cache_path + ".tmp"
        with open(temporary_path, "w", encoding="utf-8") as handle:
            json.dump(candidates, handle, ensure_ascii=False)
        os.replace(temporary_path, cache_path)
    except Exception as exc:
        xbmc.log("%s: could not save background artwork cache: %s" % (LOG_PREFIX, exc), xbmc.LOGDEBUG)



def main():
    # The service now only refreshes the Apps hub's background artwork cache.
    # Playback is not monitored, and Watchlist entries remain until manually removed.
    monitor = xbmc.Monitor()
    worker = threading.Thread(
        target=_refresh_app_artwork_cache,
        name="KodiHomeAppArtCache",
        daemon=True,
    )
    worker.start()
    store = LocalStore(xbmcaddon.Addon("plugin.video.kodihome"))
    library = _build_library_index()
    watchlist = _build_watchlist_index(store)
    next_identity_refresh = time.monotonic() + IDENTITY_REFRESH_SECONDS
    while not monitor.abortRequested():
        # Refresh membership before decorating so removals do not retain old flags.
        watchlist = _build_watchlist_index(store)
        if time.monotonic() >= next_identity_refresh:
            library = _build_library_index()
            next_identity_refresh = time.monotonic() + IDENTITY_REFRESH_SECONDS
        _decorate_home_widgets(library, watchlist)
        if monitor.waitForAbort(STATUS_REFRESH_SECONDS):
            break


if __name__ == "__main__":
    main()
