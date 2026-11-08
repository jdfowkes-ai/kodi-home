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
        path = os.path.join(profile, "app-brand-logos", "paramount-plus.png")
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
