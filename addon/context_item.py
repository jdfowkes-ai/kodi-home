"""Kodi global context-menu actions for Kodi Home lists."""

import hashlib
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


def main():
    if len(sys.argv) < 2 or sys.argv[1] != "add_watchlist":
        return
    selected = getattr(sys, "listitem", None)
    if selected is None:
        xbmcgui.Dialog().notification("Kodi Home", "Selected item details were unavailable")
        return
    try:
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
        unique_id = _call(tag, "getUniqueID", "")
        if unique_id:
            metadata["uniqueid"] = unique_id
        LocalStore(xbmcaddon.Addon("plugin.video.kodihome")).add_watchlist_item({
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
        xbmcgui.Dialog().notification("Kodi Home", "Could not add this item")


if __name__ == "__main__":
    main()
