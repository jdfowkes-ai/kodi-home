"""Kodi Home local lists and Kodi-library browsing interface."""

import json
import sys
from urllib.parse import parse_qs, urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib.kodihome import LocalStore


ADDON_ID = "plugin.video.kodihome"
PLUGIN_URL = "plugin://%s/" % ADDON_ID
HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon(ADDON_ID)
STORE = LocalStore(ADDON)


def _url(**params):
    return PLUGIN_URL + "?" + urlencode(params)


def _rpc(method, params):
    request = {
        "jsonrpc": "2.0",
        "id": "kodihome-ui",
        "method": method,
        "params": params,
    }
    response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if "error" in response:
        raise RuntimeError(response["error"])
    return response.get("result", {})


def _art(value):
    if not isinstance(value, dict):
        return {}
    return {
        key: value[key]
        for key in ("thumb", "poster", "fanart", "landscape", "clearlogo")
        if value.get(key)
    }


def _context(commands):
    return [(label, "RunPlugin(%s)" % target) for label, target in commands]


def _folder(label, target, art=None):
    item = xbmcgui.ListItem(label=label)
    item.setArt(_art(art))
    xbmcplugin.addDirectoryItem(HANDLE, target, item, isFolder=True)


def _video_item(label, target, info, art=None, context=None, folder=False):
    item = xbmcgui.ListItem(label=label)
    item.setInfo("video", info)
    item.setArt(_art(art))
    if not folder:
        item.setProperty("IsPlayable", "true")
    if context:
        item.addContextMenuItems(_context(context))
    xbmcplugin.addDirectoryItem(HANDLE, target, item, isFolder=folder)


def _finish(content="videos"):
    xbmcplugin.setContent(HANDLE, content)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.endOfDirectory(HANDLE)


def _notify(message):
    xbmcgui.Dialog().notification("Kodi Home", message, time=2500)


def _movie_details(movie_id):
    return _rpc(
        "VideoLibrary.GetMovieDetails",
        {
            "movieid": int(movie_id),
            "properties": ["title", "year", "premiered", "plot", "genre", "art", "file", "uniqueid"],
        },
    ).get("moviedetails")


def _show_details(show_id):
    return _rpc(
        "VideoLibrary.GetTVShowDetails",
        {
            "tvshowid": int(show_id),
            "properties": ["title", "year", "premiered", "plot", "genre", "art", "uniqueid"],
        },
    ).get("tvshowdetails")


def _episode_details(episode_id):
    return _rpc(
        "VideoLibrary.GetEpisodeDetails",
        {
            "episodeid": int(episode_id),
            "properties": [
                "title", "showtitle", "year", "season", "episode", "plot",
                "art", "file", "playcount", "tvshowid",
            ],
        },
    ).get("episodedetails")


def _library_episodes(show_id):
    result = _rpc(
        "VideoLibrary.GetEpisodes",
        {
            "tvshowid": int(show_id),
            "properties": [
                "episodeid", "title", "showtitle", "season", "episode",
                "playcount", "art", "file", "plot",
            ],
            "limits": {"start": 0, "end": 500},
            "sort": {"method": "episode", "order": "ascending"},
        },
    )
    episodes = result.get("episodes", [])
    return sorted(
        episodes,
        key=lambda entry: (
            int(entry.get("season") or 0),
            int(entry.get("episode") or 0),
        ),
    )


def _details_for_item(media_type, db_id):
    if media_type == "movie":
        return _movie_details(db_id)
    if media_type == "episode":
        return _episode_details(db_id)
    return None


def _play(path, info, art=None, start_seconds=0):
    if not path:
        _notify("This item has no playable Kodi library path")
        if HANDLE >= 0:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    item = xbmcgui.ListItem(label=info.get("title", ""), path=path)
    item.setInfo("video", info)
    item.setArt(_art(art))
    item.setProperty("IsPlayable", "true")
    if int(start_seconds or 0) > 0:
        # Kodi's ListItem StartOffset property is expressed in seconds.
        item.setProperty("StartOffset", str(int(start_seconds)))

    if HANDLE >= 0:
        xbmcplugin.setResolvedUrl(HANDLE, True, item)
    else:
        xbmc.Player().play(path, item)


def _play_library(media_type, db_id, start_seconds=0):
    details = _details_for_item(media_type, db_id)
    if not details:
        _notify("Kodi could not find this library item")
        if HANDLE >= 0:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return
    info = {
        "title": details.get("title", ""),
        "mediatype": media_type,
        "dbid": int(db_id),
        "year": details.get("year", 0),
        "plot": details.get("plot", ""),
        "genre": details.get("genre", []),
    }
    if media_type == "episode":
        info.update(
            {
                "tvshowtitle": details.get("showtitle", ""),
                "season": details.get("season", 0),
                "episode": details.get("episode", 0),
            }
        )
    _play(details.get("file", ""), info, details.get("art"), start_seconds)


def _root():
    _folder("Continue Watching", _url(action="list", name="continue"))
    _folder("Up Next", _url(action="list", name="up_next"))
    _folder("History", _url(action="list", name="history"))
    _folder("Watchlist", _url(action="watchlist"))
    _folder("Add from Kodi library", _url(action="add_library"))
    _finish()


def _continue_watching():
    for row in STORE.list_continue_watching():
        suffix = " · S%02dE%02d" % (row.get("season") or 0, row.get("episode") or 0) if row["media_type"] == "episode" else ""
        label = (row.get("show_title") + suffix + " · " if row.get("show_title") else "") + row["title"]
        info = {
            "title": row["title"],
            "mediatype": row["media_type"],
            "year": row.get("year") or 0,
            "plot": "",
            "duration": int(row.get("duration_seconds") or 0),
            "playcount": 0,
        }
        if row["media_type"] == "episode":
            info.update({"tvshowtitle": row.get("show_title", ""), "season": row.get("season") or 0, "episode": row.get("episode") or 0})
        play_url = _url(action="play_progress", key=row["item_key"], start=int(row.get("position_seconds") or 0))
        context = [
            ("Play from beginning", _url(action="play_progress", key=row["item_key"], start=0)),
            ("Remove from Continue Watching", _url(action="remove_continue", key=row["item_key"])),
        ]
        _video_item(label, play_url, info, context=context)
    _finish()


def _up_next():
    for row in STORE.list_up_next():
        label = "%s · S%02dE%02d · %s" % (
            row.get("show_title") or "TV show",
            row.get("season") or 0,
            row.get("episode") or 0,
            row["title"],
        )
        info = {
            "title": row["title"],
            "tvshowtitle": row.get("show_title", ""),
            "mediatype": "episode",
            "season": row.get("season") or 0,
            "episode": row.get("episode") or 0,
            "dbid": row["episode_db_id"],
        }
        _video_item(
            label,
            _url(action="play_library", media_type="episode", db_id=row["episode_db_id"], start=0),
            info,
            context=[("Remove from Up Next", _url(action="remove_up_next", show_id=row["tvshow_db_id"]))],
        )
    _finish()


def _history():
    for row in STORE.list_history():
        label = (row.get("show_title") + " · " if row.get("show_title") else "") + row["title"]
        info = {
            "title": row["title"],
            "mediatype": row["media_type"],
            "year": row.get("year") or 0,
            "playcount": 1,
        }
        context = [("Remove from History", _url(action="remove_history", playback_id=row["playback_id"]))]
        if row.get("kodi_db_id"):
            target = _url(action="play_library", media_type=row["media_type"], db_id=row["kodi_db_id"], start=0)
            _video_item(label, target, info, context=context)
        else:
            _video_item(label, row.get("file_path", ""), info, context=context)
    _finish()


def _watchlist():
    _folder("All", _url(action="watchlist_items", bucket="all"))
    _folder("Released", _url(action="watchlist_items", bucket="released"))
    _folder("Unreleased", _url(action="watchlist_items", bucket="unreleased"))
    _finish()


def _watchlist_items(bucket):
    for row in STORE.list_watchlist(bucket=bucket):
        info = {
            "title": row["title"],
            "mediatype": row["media_type"],
            "year": row.get("year") or 0,
        }
        context = [("Remove from Watchlist", _url(action="remove_watchlist", key=row["item_key"]))]
        if row["media_type"] == "tvshow":
            target = _url(action="watchlist_show", key=row["item_key"])
            _video_item(row["title"], target, info, art=row.get("metadata", {}).get("art"), context=context, folder=True)
        elif row.get("kodi_db_id"):
            target = _url(action="play_library", media_type="movie", db_id=row["kodi_db_id"], start=0)
            _video_item(row["title"], target, info, art=row.get("metadata", {}).get("art"), context=context)
        else:
            _video_item(row["title"], "", info, art=row.get("metadata", {}).get("art"), context=context)
    _finish()


def _watchlist_show(key):
    entries = [row for row in STORE.list_watchlist("all") if row["item_key"] == key]
    if not entries or not entries[0].get("kodi_db_id"):
        _notify("This show is not linked to a Kodi library entry")
        _finish()
        return
    for episode in _library_episodes(entries[0]["kodi_db_id"]):
        label = "%s · S%02dE%02d · %s" % (
            episode.get("showtitle") or entries[0]["title"],
            episode.get("season") or 0,
            episode.get("episode") or 0,
            episode.get("title") or "",
        )
        info = {
            "title": episode.get("title", ""),
            "tvshowtitle": episode.get("showtitle", ""),
            "mediatype": "episode",
            "season": episode.get("season", 0),
            "episode": episode.get("episode", 0),
            "dbid": episode["episodeid"],
            "plot": episode.get("plot", ""),
        }
        _video_item(
            label,
            _url(action="play_library", media_type="episode", db_id=episode["episodeid"], start=0),
            info,
            art=episode.get("art"),
        )
    _finish()


def _add_library():
    _folder("Movies", _url(action="library_items", media_type="movie"))
    _folder("TV Shows", _url(action="library_items", media_type="tvshow"))
    _finish()


def _library_items(media_type):
    if media_type == "movie":
        result = _rpc(
            "VideoLibrary.GetMovies",
            {
                "properties": ["title", "year", "premiered", "plot", "genre", "art", "file", "uniqueid"],
                "limits": {"start": 0, "end": 500},
                "sort": {"method": "title", "order": "ascending"},
            },
        )
        entries = result.get("movies", [])
        id_key = "movieid"
    else:
        result = _rpc(
            "VideoLibrary.GetTVShows",
            {
                "properties": ["title", "year", "premiered", "plot", "genre", "art", "uniqueid"],
                "limits": {"start": 0, "end": 500},
                "sort": {"method": "title", "order": "ascending"},
            },
        )
        entries = result.get("tvshows", [])
        id_key = "tvshowid"

    for entry in entries:
        db_id = entry.get(id_key)
        if not db_id:
            continue
        label = entry.get("title", "")
        target = _url(action="library_entry", media_type=media_type, db_id=db_id)
        add_target = _url(action="add_watchlist", media_type=media_type, db_id=db_id)
        info = {
            "title": label,
            "mediatype": "movie" if media_type == "movie" else "tvshow",
            "year": entry.get("year", 0),
            "plot": entry.get("plot", ""),
            "genre": entry.get("genre", []),
        }
        context = [("Add to Watchlist", add_target)]
        _video_item(label, target, info, art=entry.get("art"), context=context, folder=True)
    _finish()


def _library_entry(media_type, db_id):
    details = _movie_details(db_id) if media_type == "movie" else _show_details(db_id)
    if not details:
        _notify("Kodi could not find this library item")
        _finish()
        return
    title = details.get("title", "")
    _folder("Add %s to Watchlist" % title, _url(action="add_watchlist", media_type=media_type, db_id=db_id), details.get("art"))
    _finish()


def _add_to_watchlist(media_type, db_id):
    if media_type == "movie":
        item = _movie_details(db_id)
        release_date = item.get("premiered") if item else None
        key = "movie:%s" % db_id
        item_type = "movie"
    else:
        item = _show_details(db_id)
        release_date = item.get("premiered") if item else None
        key = "tvshow:%s" % db_id
        item_type = "tvshow"

    if not item:
        _notify("Kodi could not find this library item")
        return
    STORE.add_watchlist_item(
        {
            "item_key": key,
            "media_type": item_type,
            "kodi_db_id": int(db_id),
            "title": item.get("title", ""),
            "year": item.get("year"),
            "release_date": release_date,
            "metadata": {
                "art": item.get("art", {}),
                "uniqueid": item.get("uniqueid", {}),
            },
        }
    )
    _notify("Added to Watchlist")
    if HANDLE >= 0:
        _folder("Open Watchlist", _url(action="watchlist_items", bucket="all"))
        _finish()
    else:
        xbmc.executebuiltin("Container.Refresh")


def _remove(action, params):
    if action == "remove_continue":
        STORE.remove_continue_watching(params.get("key", ""))
    elif action == "remove_history":
        STORE.remove_history_entry(params.get("playback_id", ""))
    elif action == "remove_up_next":
        STORE.remove_up_next(int(params.get("show_id", 0)))
    elif action == "remove_watchlist":
        STORE.remove_watchlist_item(params.get("key", ""))
    _notify("List updated")
    xbmc.executebuiltin("Container.Refresh")


def main():
    query = parse_qs(sys.argv[2][1:] if len(sys.argv) > 2 else "")
    params = {key: values[0] for key, values in query.items() if values}
    action = params.get("action", "root")

    if action == "root":
        _root()
    elif action == "list" and params.get("name") == "continue":
        _continue_watching()
    elif action == "list" and params.get("name") == "up_next":
        _up_next()
    elif action == "list" and params.get("name") == "history":
        _history()
    elif action == "watchlist":
        _watchlist()
    elif action == "watchlist_items":
        _watchlist_items(params.get("bucket", "all"))
    elif action == "watchlist_show":
        _watchlist_show(params.get("key", ""))
    elif action == "add_library":
        _add_library()
    elif action == "library_items":
        _library_items(params.get("media_type", "movie"))
    elif action == "library_entry":
        _library_entry(params.get("media_type", "movie"), int(params.get("db_id", 0)))
    elif action == "add_watchlist":
        _add_to_watchlist(params.get("media_type", "movie"), int(params.get("db_id", 0)))
    elif action.startswith("remove_"):
        _remove(action, params)
    elif action == "play_progress":
        key = params.get("key", "")
        row = next((item for item in STORE.list_continue_watching(500) if item["item_key"] == key), None)
        if row:
            start = int(params.get("start", row.get("position_seconds") or 0))
            if row.get("kodi_db_id"):
                _play_library(row["media_type"], row["kodi_db_id"], start)
            else:
                _play(row["file_path"], {"title": row["title"], "mediatype": row["media_type"]}, start_seconds=start)
        elif HANDLE >= 0:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
    elif action == "play_library":
        _play_library(params.get("media_type", "episode"), int(params.get("db_id", 0)), int(params.get("start", 0)))
    else:
        if HANDLE >= 0:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        xbmc.log("Kodi Home UI failed: %s" % exc, xbmc.LOGERROR)
        if HANDLE >= 0:
            try:
                xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
            except Exception:
                xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
