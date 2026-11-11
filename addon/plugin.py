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


PARAMOUNT_PLUS_MARK_B64 = "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"


ADDON_ID = "plugin.video.kodihome"
PLUGIN_URL = "plugin://%s/" % ADDON_ID
YOUTUBE_PUBLIC_FEED_PATH = "plugin://plugin.video.youtube/special/popular_right_now"
BBC_IPLAYER_POPULAR_FEED_PATH = "plugin://plugin.video.iplayerwww/?mode=105"
APP_FEED_PATH_RE = re.compile(r"^plugin://[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./%?=&+%-]*)?$")
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


def _default_app_feed(app):
    """Return a live Kodi add-on feed preset when its provider add-on is installed."""
    package_name = str(app.get("package_name") or "")
    if package_name == "com.google.android.youtube.tv":
        return YOUTUBE_PUBLIC_FEED_PATH

    title_key = re.sub(r"[^a-z0-9]+", "", str(app.get("title") or "").casefold())
    if title_key in ("bbciplayer", "iplayer", "iplayerwww") and xbmc.getCondVisibility(
        "System.HasAddon(plugin.video.iplayerwww)"
    ):
        return BBC_IPLAYER_POPULAR_FEED_PATH
    return ""


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
    """Return white brand artwork, using the Paramount+ mountain-and-stars mark."""
    title = str(app.get("title") or "").casefold()
    key = re.sub(r"[^a-z0-9]+", "", title)
    filename = APP_CLEARLOGO_FILES.get(key)
    if not filename:
        return ""

    if key in ("paramount", "paramountplus"):
        profile = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
        path = os.path.join(profile, "app-brand-logos", "paramount-plus-mark.png")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.isfile(path):
                with open(path, "wb") as handle:
                    handle.write(base64.b64decode(PARAMOUNT_PLUS_MARK_B64))
            if xbmcvfs.exists(path):
                return path
        except Exception as exc:
            xbmc.log("Kodi Home: could not create Paramount+ logo mark: %s" % exc, xbmc.LOGDEBUG)

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
                if not is_paramount or basename not in ("paramount-plus.png", "paramount-plus-v2.png", "paramount-plus-mark.png"):
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
        feed_path = (app.get("feed_path") or _default_app_feed(app)).strip()
        reload_key = "%s:%s" % (package_name, int(time.time()))
        spotlight_label = label
        if package_name == "com.google.android.youtube.tv":
            spotlight_label = "YouTube Trending"
        elif feed_path:
            spotlight_label = "%s Feed" % label
        if feed_path:
            item.setProperty("KodiHome.LiveFeedPath", feed_path)
            # Arctic Fuse reads these item properties to replace its Home hero
            # with the selected app's live add-on feed.
            item.setProperty("app_spotlight_path", feed_path)
            item.setProperty("app_spotlight_label", spotlight_label)
            item.setProperty("app_spotlight_reload", reload_key)
        item.setProperty("KodiHome.SpotlightLogo", app_art.get("clearlogo", ""))
        item.setProperty("KodiHome.SpotlightBackdrop", app_art.get("fanart", ""))
        item.setProperty("KodiHome.SpotlightLabel", label)
        item.setProperty("KodiHome.SpotlightReload", reload_key)
        # Keep the property names expected by Arctic Fuse's app spotlight.
        item.setProperty("app_spotlight_logo", app_art.get("clearlogo", ""))
        item.setProperty("app_spotlight_blur", app_art.get("fanart", ""))
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
            ("Browse Kodi folders for live content feed", _url(
                action="app_browse_feed",
                package=package_name,
            )),
            ("Enter live content feed path", _url(
                action="app_edit_feed",
                package=package_name,
            )),
            *([("Use YouTube public feed", _url(
                action="app_youtube_feed",
                package=package_name,
            ))] if package_name == "com.google.android.youtube.tv" else []),
            *([("Use BBC iPlayer popular feed", _url(
                action="app_iplayer_feed",
                package=package_name,
            ))] if _default_app_feed(app) == BBC_IPLAYER_POPULAR_FEED_PATH else []),
            ("Open live content feed", _url(
                action="app_open_feed",
                package=package_name,
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


def _browse_app_feed(params):
    package_name = params.get("package", "")
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        _notify("Invalid Android package name")
        return
    app = next((row for row in STORE.list_apps() if row["package_name"] == package_name), None)
    if not app:
        _notify("App not found")
        return

    # Start at Kodi's Videos shortcut root, where Add-ons is one of the
    # visible choices. A non-plugin root path also lets cancellation be
    # distinguished from a selected add-on folder.
    browse_root = "library://video/"
    selected = xbmcgui.Dialog().browse(
        0,
        "Choose a folder inside a Kodi video add-on",
        "video",
        "",
        False,
        False,
        browse_root,
    )
    if not selected:
        return
    selected = str(selected).strip()
    # Kodi returns the default path when the browser is closed without a choice.
    if selected == browse_root:
        return
    if not APP_FEED_PATH_RE.fullmatch(selected):
        _notify("Choose a folder inside a Kodi video add-on")
        return

    STORE.update_app_feed(package_name, selected)
    _notify("Live content feed saved")
    xbmc.executebuiltin("Container.Refresh")


def _edit_app_feed(params):
    package_name = params.get("package", "")
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        _notify("Invalid Android package name")
        return
    app = next((row for row in STORE.list_apps() if row["package_name"] == package_name), None)
    if not app:
        _notify("App not found")
        return
    default_path = app.get("feed_path") or _default_app_feed(app)
    feed_path = xbmcgui.Dialog().input(
        "Kodi content feed path",
        defaultt=default_path,
    ).strip()
    if feed_path and not APP_FEED_PATH_RE.fullmatch(feed_path):
        _notify("Enter a Kodi plugin:// feed path")
        return
    STORE.update_app_feed(package_name, feed_path)
    _notify("Live content feed saved" if feed_path else "Live content feed cleared")
    xbmc.executebuiltin("Container.Refresh")


def _use_youtube_public_feed(params):
    package_name = params.get("package", "")
    if package_name != "com.google.android.youtube.tv":
        _notify("This preset is for the YouTube app")
        return
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        _notify("Invalid Android package name")
        return
    STORE.update_app_feed(package_name, YOUTUBE_PUBLIC_FEED_PATH)
    _notify("YouTube public feed set")
    xbmc.executebuiltin("Container.Refresh")


def _use_bbc_iplayer_popular_feed(params):
    package_name = params.get("package", "")
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        _notify("Invalid Android package name")
        return
    app = next((row for row in STORE.list_apps() if row["package_name"] == package_name), None)
    if not app:
        _notify("App not found")
        return
    if _default_app_feed(app) != BBC_IPLAYER_POPULAR_FEED_PATH:
        _notify("Install the Kodi iPlayer WWW add-on to use this feed")
        return
    STORE.update_app_feed(package_name, BBC_IPLAYER_POPULAR_FEED_PATH)
    _notify("BBC iPlayer popular feed set")
    xbmc.executebuiltin("Container.Refresh")


def _open_app_feed(params):
    package_name = params.get("package", "")
    if not ANDROID_PACKAGE_RE.fullmatch(package_name):
        _notify("Invalid Android package name")
        return
    app = next((row for row in STORE.list_apps() if row["package_name"] == package_name), None)
    if not app:
        _notify("App not found")
        return
    feed_path = (app.get("feed_path") or _default_app_feed(app)).strip()
    if not feed_path:
        _notify("Set a live feed path for this app first")
        return
    if not APP_FEED_PATH_RE.fullmatch(feed_path):
        _notify("The saved live feed path is invalid")
        return
    xbmc.executebuiltin("Container.Update(%s)" % feed_path)




def _refresh_app_spotlight():
    """Refresh the selected app feed and restore focus to its actual Apps row."""
    home = xbmcgui.Window(10000)
    feed_path = home.getProperty("AppSpotlight.Path").strip()
    app_control = home.getProperty("AppSpotlight.AppControl").strip()
    if not feed_path or not APP_FEED_PATH_RE.fullmatch(feed_path):
        return
    if not re.fullmatch(r"\\d{1,6}", app_control) or app_control == "301":
        xbmc.log("Kodi Home: app Spotlight refresh has no valid Apps row control", xbmc.LOGWARNING)
        return

    home.setProperty("AppSpotlight.Refreshing", "true")
    try:
        # Container.Update acts on the focused container. Focus the hidden
        # Spotlight list only after confirming Kodi accepted that focus change.
        xbmc.executebuiltin("SetFocus(301)", wait=True)
        if not xbmc.getCondVisibility("Control.HasFocus(301)"):
            raise RuntimeError("Kodi did not focus the hidden Spotlight list")
        xbmc.executebuiltin("Container.Update(%s)" % feed_path, wait=True)
    except Exception as exc:
        xbmc.log("Kodi Home: app Spotlight refresh failed: %s" % exc, xbmc.LOGWARNING)
    finally:
        # Do not steal focus back if the user moved to another app or menu
        # while the add-on feed was loading.
        still_selected = (
            home.getProperty("AppSpotlight.Path") == feed_path
            and home.getProperty("AppSpotlight.AppControl") == app_control
        )
        if still_selected:
            try:
                xbmc.executebuiltin("SetFocus(%s)" % app_control, wait=True)
            except Exception as exc:
                xbmc.log("Kodi Home: could not restore Apps row focus: %s" % exc, xbmc.LOGWARNING)
        home.clearProperty("AppSpotlight.Refreshing")



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
    elif action == "app_browse_feed":
        _browse_app_feed(params)
    elif action == "app_edit_feed":
        _edit_app_feed(params)
    elif action == "app_open_feed":
        _open_app_feed(params)
    elif action == "refresh_app_spotlight":
        _refresh_app_spotlight()
    elif action == "app_youtube_feed":
        _use_youtube_public_feed(params)
    elif action == "app_iplayer_feed":
        _use_bbc_iplayer_popular_feed(params)
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
