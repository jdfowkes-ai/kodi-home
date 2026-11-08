"""Kodi Home local lists and Kodi-library browsing interface."""

import hashlib
import json
import os
import random
import re
import sys
from urllib.parse import parse_qs, urlencode, urlparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.kodihome import LocalStore


ADDON_ID = "plugin.video.kodihome"
PLUGIN_URL = "plugin://%s/" % ADDON_ID
HANDLE = int(sys.argv[1])


APP_BACKGROUND_STUDIO_MATCHERS = {
    "netflix": ("netflix",),
    "disney+": ("disney+", "disney plus", "walt disney", "disney studios", "pixar", "marvel", "lucasfilm", "national geographic"),
    "prime video": ("prime video", "amazon studios", "amazon"),
    "amazon prime video": ("prime video", "amazon studios", "amazon"),
    "apple tv": ("apple tv+", "apple tv", "apple studios", "apple original"),
    "apple tv+": ("apple tv+", "apple tv", "apple studios", "apple original"),
    "bbc iplayer": ("bbc",),
    "itvx": ("itv",),
    "channel 4": ("channel 4", "all 4"),
    "all 4": ("channel 4", "all 4"),
    "5": ("channel 5",),
    "channel 5": ("channel 5",),
    "paramount+": ("paramount+", "paramount plus", "paramount pictures", "nickelodeon"),
    "discovery+": ("discovery+", "discovery plus", "discovery channel"),
    "now": ("sky",),
    "youtube": ("youtube originals", "youtube"),
    "youtube kids": ("youtube originals", "youtube"),
}
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


def _video_item(label, target, info, art=None, context=None, folder=False, properties=None):
    item = xbmcgui.ListItem(label=label)
    item.setInfo("video", info)
    item.setArt(_art(art))
    for key, value in (properties or {}).items():
        item.setProperty(key, str(value))
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


APP_CLEARLOGO_FILES = {
    "appletv": "apple-tv.png",
    "appletvplus": "apple-tv.png",
    "itvx": "itvx.png",
    "youtube": "youtube.png",
    "youtubekids": "youtube.png",
    "hbomax": "hbo-max.png",
    "max": "hbo-max.png",
    "channel4": "channel-4.png",
    "all4": "channel-4.png",
}


def _default_app_clearlogo(app):
    """Return bundled white brand artwork for recognized app titles."""
    title = str(app.get("title") or "").casefold()
    key = re.sub(r"[^a-z0-9]+", "", title)
    filename = APP_CLEARLOGO_FILES.get(key)
    if not filename:
        return ""
    path = xbmcvfs.translatePath(
        "special://home/addons/%s/resources/app-logos/%s" % (ADDON_ID, filename)
    )
    return path if xbmcvfs.exists(path) else ""


def _app_art(app, fallback_fanart=""):
    icon = app.get("icon_path") or ""
    return _art({
        "icon": icon,
        "thumb": icon,
        "poster": icon,
        "clearlogo": app.get("clearlogo_path") or _default_app_clearlogo(app),
        "fanart": app.get("fanart_path") or fallback_fanart,
    })


def _library_service_candidates():
    """Read Kodi library artwork and studio metadata for app-matched backdrops."""
    candidates = []
    for method, result_key in (
        ("VideoLibrary.GetMovies", "movies"),
        ("VideoLibrary.GetTVShows", "tvshows"),
    ):
        try:
            result = _rpc(method, {
                "properties": ["art", "studio"],
                "limits": {"start": 0, "end": 1000},
                "sort": {"method": "title", "order": "ascending"},
            })
            candidates.extend(result.get(result_key, []))
        except Exception as exc:
            xbmc.log(
                "Kodi Home: app backdrop library lookup failed for %s: %s" % (method, exc),
                xbmc.LOGDEBUG,
            )
    return candidates


def _matching_app_fanart_matches(app, candidates):
    """Return unique fanart URLs whose studio metadata matches this app brand."""
    app_name = str(app.get("title") or "").strip().casefold()
    terms = APP_BACKGROUND_STUDIO_MATCHERS.get(app_name, ())
    if not terms:
        return []

    matches = []
    for entry in candidates:
        studios = entry.get("studio") or []
        if not isinstance(studios, (list, tuple)):
            studios = [studios]
        studio_text = " ".join(str(studio) for studio in studios).casefold()
        if not any(term in studio_text for term in terms):
            continue
        fanart = (entry.get("art") or {}).get("fanart")
        if fanart and fanart not in matches:
            matches.append(fanart)
    return matches


def _matching_app_fanart(app, candidates):
    if app.get("fanart_path"):
        return ""
    matches = _matching_app_fanart_matches(app, candidates)
    return random.choice(matches) if matches else ""


def _matching_app_fanart_folder(app, candidates):
    """Cache a small rotating set of matching Kodi-library fanart for the skin."""
    if app.get("fanart_path") or app.get("fanart_folder_path"):
        return ""

    matches = _matching_app_fanart_matches(app, candidates)
    if not matches:
        return ""

    package_name = str(app.get("package_name") or "")
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        return ""

    profile = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
    app_key = hashlib.sha1(package_name.encode("utf-8")).hexdigest()[:16]
    folder = os.path.join(profile, "app-backgrounds", app_key)
    try:
        if not xbmcvfs.mkdirs(folder) and not xbmcvfs.exists(folder):
            return ""
        existing_dirs, existing_files = xbmcvfs.listdir(folder)
        cached_count = len(existing_files)
        for fanart in random.sample(matches, min(12, len(matches))):
            if cached_count >= 12:
                break
            extension = os.path.splitext(urlparse(fanart).path)[1].lower()
            if extension not in (".jpg", ".jpeg", ".png", ".webp"):
                extension = ".jpg"
            filename = hashlib.sha1(fanart.encode("utf-8")).hexdigest() + extension
            destination = os.path.join(folder, filename)
            if xbmcvfs.exists(destination):
                continue
            try:
                if xbmcvfs.copy(fanart, destination):
                    cached_count += 1
            except Exception as exc:
                xbmc.log(
                    "Kodi Home: could not cache app fanart %s: %s" % (fanart, exc),
                    xbmc.LOGDEBUG,
                )
        return folder if cached_count else ""
    except Exception as exc:
        xbmc.log(
            "Kodi Home: could not prepare rotating app fanart: %s" % exc,
            xbmc.LOGDEBUG,
        )
        return ""


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


def _app_group_route(params):
    group_name = params.get("group_name", "")
    if group_name:
        group = STORE.get_app_group_by_name(group_name)
        _app_group(group["group_id"] if group else 0)
    else:
        _app_group(int(params.get("group_id", 0)))


def _app_group(group_id):
    group = STORE.get_app_group(group_id)
    if not group:
        _notify("App group not found")
        _app_groups()
        return

    apps = STORE.list_apps(group["group_id"])
    if not apps:
        _folder(
            "Add apps to %s" % group["name"],
            _url(action="app_picker", group_id=group["group_id"]),
        )
        _finish()
        return
    library_candidates = _library_service_candidates()
    for app in apps:
        package_name = app["package_name"]
        if not ANDROID_PACKAGE_RE.fullmatch(package_name):
            continue
        target = _url(action="launch_app", package=package_name)
        label = app.get("title") or package_name
        if label == package_name:
            label = _android_app_label(package_name)
        item = xbmcgui.ListItem(label=label, path=target)
        app_art = _app_art(app, _matching_app_fanart(app, library_candidates))
        item.setArt(app_art)
        item.setProperty("KodiHome.AppTile", "true")
        item.setProperty(
            "KodiHome.HasClearLogo",
            "true" if app_art.get("clearlogo") else "false",
        )
        background_folder = app.get("fanart_folder_path") or _matching_app_fanart_folder(app, library_candidates)
        if background_folder:
            item.setProperty("KodiHome.BackgroundFolder", background_folder)
        item.setInfo("video", {
            "title": label,
            "mediatype": "video",
            "plot": "",
        })
        item.addContextMenuItems(_context([
            ("Rename app", _url(
                action="app_rename",
                package=package_name,
                title=app["title"],
            )),
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
            ("Choose rotating background folder", _url(
                action="app_edit_background_folder",
                package=package_name,
            )),
            ("Clear rotating background folder", _url(
                action="app_edit_background_folder",
                package=package_name,
                clear="true",
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
        xbmcplugin.addDirectoryItem(HANDLE, target, item, isFolder=False)
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


def _android_app_label(package_name):
    known_apps = {
        "com.netflix.ninja": "Netflix",
        "com.disney.disneyplus": "Disney+",
        "com.amazon.amazonvideo.livingroom": "Prime Video",
        "com.google.android.youtube.tv": "YouTube",
        "com.google.android.youtube.tvkids": "YouTube Kids",
        "com.apple.atve.androidtv.appletv": "Apple TV",
        "com.bbc.iplayer": "BBC iPlayer",
        "air.ITVMobilePlayer": "ITVX",
        "com.itv.itvx": "ITVX",
        "com.channel4.android": "Channel 4",
        "com.paramountplus": "Paramount+",
    }
    if package_name in known_apps:
        return known_apps[package_name]
    parts = [part for part in package_name.split(".") if part not in (
        "com", "org", "net", "android", "tv", "app", "mobile", "client"
    )]
    return " ".join(part[:1].upper() + part[1:] for part in parts) or package_name


def _installed_app_picker(group_id):
    group = STORE.get_app_group(group_id)
    if not group:
        _notify("App group not found")
        _app_groups()
        return
    try:
        # Files.GetDirectory is rejected by Kodi's JSON-RPC remote-path
        # security check for androidapp:// URLs. Use Kodi's local VFS API.
        directories, files = xbmcvfs.listdir(ANDROID_APPS_PATH)
        package_names = sorted(set(directories + files), key=str.casefold)
    except Exception as exc:
        xbmc.log("Kodi Home: could not list Android apps: %s" % exc, xbmc.LOGWARNING)
        _notify("Could not read the installed Android apps")
        _app_group(group_id)
        return

    registered = {app["package_name"] for app in STORE.list_apps(group_id)}
    for package_name in package_names:
        package_name = str(package_name).strip("/")
        if not package_name or package_name.endswith((".png", ".apk")):
            continue
        if not ANDROID_PACKAGE_RE.fullmatch(package_name):
            continue

        label = _android_app_label(package_name)
        app_path = ANDROID_APPS_PREFIX + package_name
        icon_path = app_path + ".png"
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


def _rename_app(params):
    package_name = params.get("package", "")
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        _notify("Invalid Android package name")
        return
    current_title = params.get("title", package_name)
    title = xbmcgui.Dialog().input("Rename app", defaultt=current_title)
    if title:
        STORE.add_app(package_name, title)
        _notify("App name updated")
        xbmc.executebuiltin("Container.Refresh")


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


def _edit_app_background_folder(params):
    package_name = params.get("package", "")
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        _notify("Invalid Android package name")
        return
    if params.get("clear") == "true":
        STORE.update_app_artwork(package_name, "fanart_folder", "")
        _notify("Rotating background cleared")
        xbmc.executebuiltin("Container.Refresh")
        return

    selected = xbmcgui.Dialog().browseSingle(
        0,
        "Choose app background image folder",
        "pictures",
    )
    if selected:
        STORE.update_app_artwork(package_name, "fanart_folder", selected)
        _notify("Rotating background folder saved")
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


def _refresh_watchlist_metadata():
    """Refresh saved Watchlist rows from their current Kodi library entries."""
    for row in STORE.list_watchlist("all"):
        db_id = row.get("kodi_db_id")
        if not db_id:
            continue
        try:
            if row["media_type"] == "movie":
                details = _movie_details(db_id)
            elif row["media_type"] == "tvshow":
                details = _show_details(db_id)
            else:
                details = None
            if not details:
                continue
            metadata = row.get("metadata") or {}
            metadata["art"] = details.get("art") or metadata.get("art", {})
            metadata["uniqueid"] = details.get("uniqueid") or metadata.get("uniqueid", {})
            STORE.refresh_watchlist_metadata({
                "item_key": row["item_key"],
                "title": details.get("title") or row["title"],
                "year": details.get("year") or row.get("year"),
                "release_date": details.get("premiered") or row.get("release_date"),
                "metadata": metadata,
            })
        except Exception as exc:
            xbmc.log(
                "Kodi Home: watchlist metadata refresh failed for %s: %s" % (row.get("item_key"), exc),
                xbmc.LOGDEBUG,
            )


def _watchlist_items(bucket):
    _refresh_watchlist_metadata()
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
        _video_item(
            label,
            target,
            info,
            art=entry.get("art"),
            context=context,
            folder=True,
            properties={"KodiHome.LibraryItem": "true"},
        )
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
        _app_group_route(params)
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
    elif action == "app_rename":
        _rename_app(params)
    elif action == "app_edit_art":
        _edit_app_art(params)
    elif action == "app_edit_background_folder":
        _edit_app_background_folder(params)
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
