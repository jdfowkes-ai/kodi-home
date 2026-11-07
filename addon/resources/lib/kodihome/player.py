"""Kodi player callbacks for local playback progress and history."""

import hashlib
import json
import time
import uuid

import xbmc


SAVE_INTERVAL_SECONDS = 30


class KodiHomePlayer(xbmc.Player):
    """Observe Kodi's confirmed AV playback and persist local progress."""

    def __init__(self, store):
        super().__init__()
        self.store = store
        self.active_item = None
        self.playback_id = None
        self.last_saved_at = 0.0
        self.log_prefix = "Kodi Home playback"

    def onAVStarted(self):
        # Kodi documents this callback as occurring once audio or video is
        # available; onPlayBackStarted may fire before a stream is available.
        self._begin_current_item()

    def onPlayBackPaused(self):
        self._save_progress(force=True)

    def onPlayBackResumed(self):
        self.last_saved_at = time.monotonic()

    def onPlayBackSeek(self, time_ms, seek_offset_ms):
        self._save_progress(force=True)

    def onPlayBackStopped(self):
        # A deliberate stop saves progress but does not mark the item complete.
        self._save_progress(force=True)
        self._clear_active_item()

    def onPlayBackEnded(self):
        item = self._read_current_item() or self.active_item
        if item is not None:
            if item["duration_seconds"] > 0:
                item["position_seconds"] = item["duration_seconds"]
            playback_id = self.playback_id or uuid.uuid4().hex
            try:
                self.store.mark_completed(item, playback_id)
                if item["media_type"] == "episode":
                    self._refresh_up_next(item)
            except Exception as exc:
                xbmc.log("%s: could not save completion: %s" % (self.log_prefix, exc), xbmc.LOGERROR)
        self._clear_active_item()

    def tick(self):
        """Poll during playback and save at the configured interval."""
        try:
            if not self.isPlaying():
                return
            item = self._read_current_item()
            if item is None:
                return
            if self.active_item is None or item["item_key"] != self.active_item["item_key"]:
                self._begin_current_item(item)
            self._save_progress(force=False, item=item)
        except Exception as exc:
            xbmc.log("%s: playback poll failed: %s" % (self.log_prefix, exc), xbmc.LOGWARNING)

    def _begin_current_item(self, item=None):
        item = item or self._read_current_item()
        if item is None:
            return
        self._set_active_item(item)
        try:
            removed = self.store.remove_watchlist_for_playback(item)
            if removed:
                xbmc.log(
                    "%s: removed started item from Watchlist: %s"
                    % (self.log_prefix, item["title"]),
                    xbmc.LOGINFO,
                )
        except Exception as exc:
            # Playback still proceeds if local Watchlist maintenance fails.
            xbmc.log(
                "%s: could not update Watchlist after confirmed start: %s"
                % (self.log_prefix, exc),
                xbmc.LOGERROR,
            )
        xbmc.log("%s: confirmed start for %s" % (self.log_prefix, item["title"]), xbmc.LOGINFO)

    def _refresh_up_next(self, completed_item):
        """Select the next unwatched Kodi-library episode for this show."""
        show_db_id = completed_item.get("tvshow_db_id")
        if not show_db_id:
            return
        request = {
            "jsonrpc": "2.0",
            "id": "kodihome-up-next",
            "method": "VideoLibrary.GetEpisodes",
            "params": {
                "tvshowid": show_db_id,
                "properties": [
                    "episodeid",
                    "title",
                    "showtitle",
                    "season",
                    "episode",
                    "playcount",
                    "file",
                ],
                "limits": {"start": 0, "end": 500},
            },
        }
        try:
            response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
            episodes = response.get("result", {}).get("episodes", [])
            current_order = (
                int(completed_item.get("season") or 0),
                int(completed_item.get("episode") or 0),
            )
            candidates = [
                episode
                for episode in episodes
                if episode.get("episodeid")
                and (
                    int(episode.get("season") or 0),
                    int(episode.get("episode") or 0),
                )
                > current_order
            ]
            candidates.sort(
                key=lambda episode: (
                    int(episode.get("season") or 0),
                    int(episode.get("episode") or 0),
                )
            )
            for episode in candidates:
                if int(episode.get("playcount") or 0) > 0:
                    continue
                episode_key = "episode:%s" % episode["episodeid"]
                if self.store.is_completed(episode_key):
                    continue
                self.store.set_up_next(
                    show_db_id, completed_item["item_key"], episode
                )
                return
            self.store.clear_up_next(show_db_id)
        except Exception as exc:
            xbmc.log(
                "%s: could not refresh Up Next: %s" % (self.log_prefix, exc),
                xbmc.LOGWARNING,
            )

    def _set_active_item(self, item):
        self.active_item = item
        self.playback_id = uuid.uuid4().hex
        self.last_saved_at = time.monotonic()

    def _save_progress(self, force=False, item=None):
        if item is None:
            item = self._read_current_item() or self.active_item
        if item is None:
            return
        now = time.monotonic()
        if not force and now - self.last_saved_at < SAVE_INTERVAL_SECONDS:
            return
        if item["position_seconds"] <= 0:
            return
        try:
            self.store.save_progress(item)
            self.active_item = item
            self.last_saved_at = now
        except Exception as exc:
            xbmc.log("%s: could not save progress: %s" % (self.log_prefix, exc), xbmc.LOGERROR)

    def _read_current_item(self):
        try:
            file_path = self.getPlayingFile()
            list_item = self.getPlayingItem()
            tag = list_item.getVideoInfoTag()
            media_type = (tag.getMediaType() or "").lower()
            if media_type not in ("movie", "episode") or not file_path:
                return None

            kodi_db_id = int(tag.getDbId() or 0) or None
            item_key = "%s:%s" % (media_type, kodi_db_id) if kodi_db_id else self._path_key(media_type, file_path)
            duration = max(0.0, float(self.getTotalTime()))
            current_time = max(0.0, float(self.getTime()))
            position = min(current_time, duration) if duration else current_time
            return {
                "item_key": item_key,
                "media_type": media_type,
                "kodi_db_id": kodi_db_id,
                "tvshow_db_id": int(xbmc.getInfoLabel("VideoPlayer.TvShowDBID") or 0) or None
                if media_type == "episode"
                else None,
                "title": tag.getTitle() or file_path.rsplit("/", 1)[-1],
                "show_title": tag.getTVShowTitle() or "",
                "year": int(tag.getYear() or 0) or None,
                "season": int(tag.getSeason() or 0) or None,
                "episode": int(tag.getEpisode() or 0) or None,
                "file_path": file_path,
                "position_seconds": position,
                "duration_seconds": duration,
            }
        except Exception:
            return None

    @staticmethod
    def _path_key(media_type, file_path):
        digest = hashlib.sha256(file_path.encode("utf-8")).hexdigest()
        return "%s:path:%s" % (media_type, digest)

    def _clear_active_item(self):
        self.active_item = None
        self.playback_id = None
        self.last_saved_at = 0.0
