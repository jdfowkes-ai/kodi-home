"""Kodi Home local lists and Kodi-library browsing interface."""

import base64
import hashlib
import json
import os
import random
import re
import sys
import time
from urllib.parse import parse_qs, urlencode, urlparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.kodihome import LocalStore


PARAMOUNT_PLUS_WORDMARK_B64 = "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"


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
    "netflix": "netflix.png",
    "disneyplus": "disney-plus.png",
    "disney": "disney-plus.png",
    "primevideo": "prime-video.png",
    "amazonprimevideo": "prime-video.png",
    "appletv": "apple-tv.png",
    "appletvplus": "apple-tv.png",
    "bbciplayer": "bbc-iplayer.png",
    "itvx": "itvx.png",
    "youtube": "youtube.png",
    "youtubekids": "youtube.png",
    "hbomax": "hbo-max.png",
    "max": "hbo-max.png",
    "channel4": "channel-4.png",
    "all4": "channel-4.png",
    "now": "now.png",
    "paramountplus": "paramount-plus.png",
    "paramount": "paramount-plus.png",
}


def _default_app_clearlogo(app):
    """Return white brand artwork, generating the Paramount+ wordmark if needed."""
    title = str(app.get("title") or "").casefold()
    key = re.sub(r"[^a-z0-9]+", "", title)
    filename = APP_CLEARLOGO_FILES.get(key)
    if not filename:
        return ""

    if key in ("paramount", "paramountplus"):
        profile = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
        path = os.path.join(profile, "app-brand-logos", "paramount-plus-v2.png")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.isfile(path):
                with open(path, "wb") as handle:
                    handle.write(base64.b64decode(PARAMOUNT_PLUS_WORDMARK_B64))
            if xbmcvfs.exists(path):
                return path
        except Exception as exc:
            xbmc.log("Kodi Home: could not create Paramount+ wordmark: %s" % exc, xbmc.LOGDEBUG)

    addon_path = xbmcvfs.translatePath(ADDON.getAddonInfo("path"))
    path = os.path.join(addon_path, "resources", "app-logos", filename)
    return path if xbmcvfs.exists(path) else ""


def _app_clearlogo(app):
    """Use valid custom artwork except for a stale Paramount+ bundled-logo path."""
    custom_path = str(app.get("clearlogo_path") or "").strip()
    title_key = re.sub(r"[^a-z0-9]+", "", str(app.get("title") or "").casefold())
    if custom_path:
        is_paramount = title_key in ("paramount", "paramountplus")
        if custom_path.startswith(("http://", "https://", "image://")):
            return custom_path
        else:
            translated = xbmcvfs.translatePath(custom_path)
            if xbmcvfs.exists(translated):
                basename = os.path.basename(translated).casefold()
                if not is_paramount or basename != "paramount-plus.png":
                    return translated
    return _default_app_clearlogo(app)


def _app_art(app, fallback_fanart=""):
    icon = app.get("icon_path") or ""
    return _art({
        "icon": icon,
        "thumb": icon,
        "poster": icon,
        "clearlogo": _app_clearlogo(app),
        "fanart": app.get("fanart_path") or fallback_fanart,
    })


def _library_service_candidates():
    """Return cached Kodi artwork without blocking home-widget loading on a library scan."""
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
    cache_path = os.path.join(profile, "app-library-fanart-cache.json")
    try:
        if os.path.isfile(cache_path) and time.time() - os.path.getmtime(cache_path) < APP_LIBRARY_FANART_CACHE_SECONDS:
            with open(cache_path, "r", encoding="utf-8") as handle:
                cached = json.load(handle)
            if isinstance(cached, list):
                return cached
    except Exception as exc:
        xbmc.log("Kodi Home: app fanart cache read failed: %s" % exc, xbmc.LOGDEBUG)

    # The service refreshes this cache in the background after Kodi has settled.
    return []

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
        if cached_count:
            return folder
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
