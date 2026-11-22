"""Kodi global context-menu actions for Kodi Home lists."""

import hashlib
import json
import sys

import xbmc
import xbmcaddon
import xbmcgui

from resources.lib.kodihome import LocalStore


def _call(tag, name, default=None):
    try:
        value = getattr(tag, name)()
        return value if value not in (None, "", [], 0) else default
    except Exception:
        return default


def _remove_library_entry(selected):
    """Remove Kodi's database entry; never delete unverified .strm files."""
    tag = selected.getVideoInfoTag()
    media_type = str(_call(tag, "getMediaType", "")).lower()
    db_id = int(_call(tag, "getDbId", 0) or 0)
    if media_type not in ("movie", "tvshow") or db_id <= 0:
        xbmcgui.Dialog().notification("Kodi Home", "No matching Kodi library entry")
        return
    title = str(_call(tag, "getTitle", "") or selected.getLabel() or "this title")
    if not xbmcgui.Dialog().yesno("Remove from Kodi Library",
        'Remove "%s" from Kodi Library? The .strm shortcut will not be deleted.' % title):
        return
    method = "VideoLibrary.RemoveMovie" if media_type == "movie" else "VideoLibrary.RemoveTVShow"
    id_key = "movieid" if media_type == "movie" else "tvshowid"
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": {id_key: db_id}}
    response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if response.get("error"):
        raise RuntimeError(response["error"])
    xbmcgui.Dialog().notification("Kodi Home", "Removed library entry: " + title)


def main():
    if len(sys.argv) < 2:
        return
    action = sys.argv[1]
    if action not in ("manage_watchlist", "add_watchlist", "remove_watchlist", "remove_library"):
        return
    selected = getattr(sys, "listitem", None)
    if selected is None:
        xbmcgui.Dialog().notification("Kodi Home", "Selected item details were unavailable")
        return
    try:
        if action == "remove_library":
            _remove_library_entry(selected)
            return
        tag = selected.getVideoInfoTag()
        media_type = str(_call(tag, "getMediaType", "")).lower()
        if media_type not in ("movie", "tvshow"):
            xbmcgui.Dialog().notification("Kodi Home", "Watchlist supports movies and TV shows")
            return
        title = str(_call(tag, "getTitle", "") or selected.getLabel() or "").strip()
        if not title:
            xbmcgui.Dialog().notification("Kodi Home", "This item has no title")
            return
        year = _call(tag, "getYear")
        year = int(year) if year else None
        db_id = int(_call(tag, "getDbId", 0) or 0)
        db_id = db_id if db_id > 0 else None
        source_path = str(selected.getPath() or "")
        stable = "%s\\n%s\\n%s\\n%s" % (media_type, db_id or "", source_path, title.casefold())
        item_key = "%s:%s" % (media_type, db_id) if db_id else "%s:external:%s" % (
            media_type,
            hashlib.sha256(stable.encode("utf-8")).hexdigest(),
        )
        metadata = {
            "source_path": source_path if source_path.startswith("plugin://") else "",
            "art": {key: selected.getArt(key) for key in ("thumb", "poster", "fanart", "clearlogo", "icon") if selected.getArt(key)},
            "plot": _call(tag, "getPlot", ""),
            "genre": _call(tag, "getGenres", []),
        }
        unique_ids = _call(tag, "getUniqueIDs", {})
        if isinstance(unique_ids, dict) and unique_ids:
            metadata["uniqueid"] = unique_ids
        else:
            unique_id = _call(tag, "getUniqueID", "")
            if unique_id:
                metadata["uniqueid"] = unique_id
        store = LocalStore(xbmcaddon.Addon("plugin.video.kodihome"))
        # Match exact IDs first. Never infer identity from title alone.
        existing = None
        for row in store.list_watchlist("all"):
            if row["media_type"] != media_type:
                continue
            row_meta = row.get("metadata") or {}
            if db_id and int(row.get("kodi_db_id") or 0) == db_id:
                existing = row
                break
            row_ids = row_meta.get("uniqueid")
            if isinstance(unique_ids, dict) and isinstance(row_ids, dict):
                if any(
                    str(unique_ids.get(provider) or "") == str(row_ids.get(provider) or "")
                    for provider in ("tmdb", "imdb", "tvdb")
                    if unique_ids.get(provider) and row_ids.get(provider)
                ):
                    existing = row
                    break
            if source_path.startswith("plugin://") and row_meta.get("source_path") == source_path:
                existing = row
                break
        if action == "manage_watchlist":
            action = "remove_watchlist" if existing else "add_watchlist"
            verb = "Remove from Watchlist" if existing else "Add to Watchlist"
            if not xbmcgui.Dialog().yesno("Kodi Home", '%s: "%s"?' % (verb, title)):
                return
        if action == "remove_watchlist":
            if not existing:
                xbmcgui.Dialog().notification("Kodi Home", "Not in Watchlist: " + title)
                return
            store.remove_watchlist_item(existing["item_key"])
            xbmcgui.Dialog().notification("Kodi Home", "Removed from Watchlist: " + title)
            return
        if existing:
            xbmcgui.Dialog().notification("Kodi Home", "Already in Watchlist: " + title)
            return
        store.add_watchlist_item({
            "item_key": item_key,
            "media_type": media_type,
            "kodi_db_id": db_id,
            "title": title,
            "year": year,
            "release_date": str(_call(tag, "getPremiered", "") or "") or None,
            "metadata": metadata,
        })
        xbmcgui.Dialog().notification("Kodi Home", "Added to Watchlist: " + title)
    except Exception as exc:
        xbmc.log("Kodi Home context item failed: %s" % exc, xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Kodi Home", "Could not update this item")


if __name__ == "__main__":
    main()
