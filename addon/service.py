"""Kodi Home background service entry point."""

import json
import os
import threading
import time

import xbmc
import xbmcaddon
import xbmcvfs



ADDON = xbmcaddon.Addon()
LOG_PREFIX = "Kodi Home"
APP_ART_CACHE_SECONDS = 6 * 60 * 60


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
    worker = threading.Thread(
        target=_refresh_app_artwork_cache,
        name="KodiHomeAppArtCache",
        daemon=False,
    )
    worker.start()
    worker.join()


if __name__ == "__main__":
    main()
