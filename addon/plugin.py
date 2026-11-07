"""Kodi Home local lists and Kodi-library browsing interface."""

import json
import re
import sys
from urllib.parse import parse_qs, urlencode, urlparse

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
        for key in ("icon", "thumb", "poster", "fanart", "landscape", "clearlogo")
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
    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)


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


ANDROID_APPS_PATH = "androidapp://sources/apps/"
ANDROID_APPS_PREFIX = ANDROID_APPS_PATH
ANDROID_PACKAGE_RE = re.compile(r"^[A-Za-z0-9._]+$")


def _app_art(app):
    icon = app.get("icon_path") or ""
    return _art({
        "icon": icon,
        "thumb": icon,
        "poster": icon,
        "clearlogo": app.get("clearlogo_path") or icon,
        "fanart": app.get("fanart_path") or "",
    })


def _app_folder(label, target, context=None):
    item = xbmcgui.ListItem(label=label)
    if context:
        item.addContextMenuItems(_context(context))
    xbmcplugin.addDirectoryItem(HANDLE, target, item, isFolder=True)


def _app_groups():
    groups = STORE.list_app_groups()
    _folder("Create app group", _url(action="app_create_group"))
    _folder("Add installed app", _url(action="app_choose_group"))
    for group in groups:
        label = "%s (%d)" % (group["name"], group["app_count"])
        context = [
            ("Rename group", _url(action="app_rename_group", group_id=group["group_id"])),
            ("Delete group", _url(action="app_delete_group", group_id=group["group_id"])),
        ]
        _app_folder(
            label,
            _url(action="app_group", group_id=group["group_id"]),
            context,
        )
    _finish()


def _app_group(group_id):
    group = STORE.get_app_group(group_id)
    if not group:
        _notify("App group not found")
        _app_groups()
        return

    _folder(
        "Add installed app",
        _url(action="app_picker", group_id=group["group_id"]),
    )
    _folder(
        "Rename group",
        _url(action="app_rename_group", group_id=group["group_id"]),
    )

    for app in STORE.list_apps(group["group_id"]):
        package_name = app["package_name"]
        if not ANDROID_PACKAGE_RE.fullmatch(package_name):
            continue
        app_path = ANDROID_APPS_PREFIX + package_name
        item = xbmcgui.ListItem(label=app["title"], path=app_path)
        item.setArt(_app_art(app))
        item.setInfo("video", {
            "title": app["title"],
            "mediatype": "video",
            "plot": "",
        })
        item.addContextMenuItems(_context([
            ("Change app logo", _url(
                action="app_edit_art",
                package=package_name,
                field="clearlogo",
            )),
            ("Change app background", _url(
                action="app_edit_art",
                package=package_name,
                field="fanart",
            )),
            ("Remove from this group", _url(
                action="app_remove",
                package=package_name,
                group_id=group["group_id"],
            )),
            ("Remove app everywhere", _url(
                action="app_remove",
                package=package_name,
            )),
        ]))
        xbmcplugin.addDirectoryItem(HANDLE, app_path, item, isFolder=False)
    _finish()


def _create_app_group():
    name = xbmcgui.Dialog().input("New app group")
    if name:
        try:
            STORE.add_app_group(name)
            _notify("App group created")
        except Exception as exc:
            xbmc.log("Kodi Home: could not create app group: %s" % exc, xbmc.LOGWARNING)
            _notify("Could not create app group")
    _app_groups()


def _rename_app_group(group_id):
    group = STORE.get_app_group(group_id)
    if group:
        name = xbmcgui.Dialog().input(
            "Rename app group",
            defaultt=group["name"],
        )
        if name:
            try:
                STORE.rename_app_group(group_id, name)
                _notify("App group updated")
            except Exception as exc:
                xbmc.log("Kodi Home: could not rename app group: %s" % exc, xbmc.LOGWARNING)
                _notify("Could not rename app group")
    _app_groups()


def _delete_app_group(group_id):
    group = STORE.get_app_group(group_id)
    if group and xbmcgui.Dialog().yesno(
        "Delete app group",
        "Remove '%s' and its group membership?" % group["name"],
    ):
        STORE.remove_app_group(group_id)
        _notify("App group deleted")
    _app_groups()


def _choose_app_group():
    groups = STORE.list_app_groups()
    if not groups:
        _create_app_group()
        groups = STORE.list_app_groups()
    if not groups:
        _finish()
        return

    selected = xbmcgui.Dialog().select(
        "Choose app group",
        [group["name"] for group in groups],
    )
    if selected >= 0:
        _installed_app_picker(groups[selected]["group_id"])
    else:
        _app_groups()


def _installed_app_picker(group_id):
    group = STORE.get_app_group(group_id)
    if not group:
        _notify("App group not found")
        _app_groups()
        return
    try:
        result = _rpc(
            "Files.GetDirectory",
            {
                "directory": ANDROID_APPS_PATH,
                "media": "files",
                "properties": ["thumbnail"],
                "sort": {"method": "label", "order": "ascending"},
            },
        )
        entries = result.get("files", [])
    except Exception as exc:
        xbmc.log("Kodi Home: could not list Android apps: %s" % exc, xbmc.LOGWARNING)
        _notify("Could not read the installed Android apps")
        _app_group(group_id)
        return

    registered = {app["package_name"] for app in STORE.list_apps(group_id)}
    for entry in entries:
        app_path = str(entry.get("file") or "")
        if not app_path.startswith(ANDROID_APPS_PREFIX):
            continue
        package_name = app_path[len(ANDROID_APPS_PREFIX):].strip("/")
        if not package_name or package_name.endswith(".png"):
            continue
        if not ANDROID_PACKAGE_RE.fullmatch(package_name):
            continue

        label = str(entry.get("label") or entry.get("title") or package_name)
        icon_path = str(entry.get("thumbnail") or (app_path + ".png"))
        added = package_name in registered
        display_label = label + ("  ✓" if added else "")
        item = xbmcgui.ListItem(label=display_label)
        item.setArt({"icon": icon_path, "thumb": icon_path})
        item.setInfo("video", {
            "title": label,
            "mediatype": "video",
            "plot": "Installed Android app",
        })
        target = _url(
            action="app_add",
            group_id=group_id,
            package=package_name,
            label=label,
            icon=icon_path,
        )
        item.addContextMenuItems(_context([
            ("Add to %s" % group["name"], target),
        ]))
        xbmcplugin.addDirectoryItem(HANDLE, target, item, isFolder=True)
    _finish()


def _add_installed_app(params):
    group_id = int(params.get("group_id", 0))
    package_name = params.get("package", "")
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        _notify("Invalid Android package name")
        _installed_app_picker(group_id)
        return
    group = STORE.get_app_group(group_id)
    if not group:
        _notify("App group not found")
        _app_groups()
        return
    STORE.add_app(
        package_name,
        params.get("label", package_name),
        params.get("icon", ""),
        group_id,
    )
    _notify("Added to %s" % group["name"])
    _installed_app_picker(group_id)


def _remove_app(params):
    package_name = params.get("package", "")
    group_id = params.get("group_id")
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        _notify("Invalid Android package name")
        return
    removed = STORE.remove_app(
        package_name,
        int(group_id) if group_id else None,
    )
    _notify("App removed" if removed else "App was not in that group")
    xbmc.executebuiltin("Container.Refresh")


def _edit_app_art(params):
    package_name = params.get("package", "")
    field = params.get("field", "")
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        _notify("Invalid Android package name")
        return
    if field not in ("clearlogo", "fanart"):
        _notify("Unsupported app artwork type")
        return
    heading = "Choose white app logo" if field == "clearlogo" else "Choose app background"
    selected = xbmcgui.Dialog().browseSingle(
        2,
        heading,
        "files",
        ".png|.jpg|.jpeg|.webp",
        True,
        False,
    )
    if selected:
        STORE.update_app_artwork(package_name, field, selected)
        _notify("App artwork updated")
        xbmc.executebuiltin("Container.Refresh")


def _root():
    _folder("Apps", _url(action="apps"))
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
        _video_item(label, play_url, info, art=row.get("art"), context=context)
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
            art=row.get("art"),
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
            _video_item(label, target, info, art=row.get("art"), context=context)
        else:
            _video_item(label, row.get("file_path", ""), info, art=row.get("art"), context=context)
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
            "release_date": release_date or None,
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
    query = parse_qs(urlparse(sys.argv[2]).query if len(sys.argv) > 2 else "")
    params = {key: values[0] for key, values in query.items() if values}
    action = params.get("action", "root")

    if action == "root":
        _root()
    elif action == "apps":
        _app_groups()
    elif action == "app_group":
        _app_group(int(params.get("group_id", 0)))
    elif action == "app_create_group":
        _create_app_group()
    elif action == "app_rename_group":
        _rename_app_group(int(params.get("group_id", 0)))
    elif action == "app_delete_group":
        _delete_app_group(int(params.get("group_id", 0)))
    elif action == "app_choose_group":
        _choose_app_group()
    elif action == "app_picker":
        _installed_app_picker(int(params.get("group_id", 0)))
    elif action == "app_add":
        _add_installed_app(params)
    elif action == "app_remove":
        _remove_app(params)
    elif action == "app_edit_art":
        _edit_app_art(params)
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
    elif action == "launch_app":
        package_name = params.get("package", "")
        if ANDROID_PACKAGE_RE.fullmatch(package_name):
            xbmc.executebuiltin("StartAndroidActivity(%s)" % package_name)
        else:
            _notify("Invalid Android package name")
        _finish()
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
