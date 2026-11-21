"""Kodi player callbacks for local playback progress and history."""

import hashlib
import json
import time
import uuid
from urllib.parse import parse_qs, urlencode, urlparse

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
        self.tvshow_id_cache = {}

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
            self.store.show_continue_watching(item["item_key"])
            if item["media_type"] == "episode":
                if item.get("kodi_db_id"):
                    self.store.consume_up_next_episode(item["kodi_db_id"])
                self.store.consume_up_next_metadata(
                    item.get("show_title"), item.get("season"), item.get("episode")
                )
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

    def _resolve_tvshow_id_from_episode(self, episode_db_id):
        """Resolve the parent show directly from Kodi's current episode metadata."""
        if not episode_db_id:
            return None
        request = {
            "jsonrpc": "2.0",
            "id": "kodihome-up-next-episode",
            "method": "VideoLibrary.GetEpisodeDetails",
            "params": {
                "episodeid": int(episode_db_id),
                "properties": ["tvshowid", "showtitle", "season", "episode"],
            },
        }
        try:
            response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
            details = response.get("result", {}).get("episodedetails") or {}
            return int(details.get("tvshowid") or 0) or None
        except Exception as exc:
            xbmc.log("%s: episode parent lookup failed: %s" % (self.log_prefix, exc), xbmc.LOGDEBUG)
            return None

    def _resolve_tvshow_db_id(self, show_title):
        """Resolve a stream's show title to its local library ID when possible."""
        import re

        normalized = re.sub(r"[^a-z0-9]+", "", str(show_title or "").casefold())
        if not normalized:
            return None
        if normalized in self.tvshow_id_cache:
            return self.tvshow_id_cache[normalized] or None
        request = {
            "jsonrpc": "2.0",
            "id": "kodihome-up-next-show",
            "method": "VideoLibrary.GetTVShows",
            "params": {
                "properties": ["title"],
                "limits": {"start": 0, "end": 1000},
            },
        }
        try:
            response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
            shows = response.get("result", {}).get("tvshows", [])
            match = next(
                (row for row in shows
                 if re.sub(r"[^a-z0-9]+", "", str(row.get("title") or "").casefold()) == normalized),
                None,
            )
            show_id = int(match.get("tvshowid") or 0) if match else 0
        except Exception as exc:
            xbmc.log("%s: show lookup failed for %s: %s" %
                     (self.log_prefix, show_title, exc), xbmc.LOGDEBUG)
            show_id = 0
        self.tvshow_id_cache[normalized] = show_id
        return show_id or None

    def _umbrella_queued_next(self, completed_item):
        """Read the next Umbrella episode from Kodi's video playlist metadata."""
        request = {
            "jsonrpc": "2.0",
            "id": "kodihome-umbrella-next",
            "method": "Playlist.GetItems",
            "params": {
                "playlistid": 1,
                "properties": [
                    "title", "file", "showtitle", "season", "episode",
                    "art", "plot", "year", "mediatype",
                ],
            },
        }
        try:
            response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
            if "error" in response:
                raise RuntimeError(response["error"])
            rows = response.get("result", {}).get("items", [])
        except Exception as exc:
            xbmc.log("%s: Umbrella playlist lookup failed: %s" % (self.log_prefix, exc), xbmc.LOGDEBUG)
            return None

        import re
        normalize = lambda value: re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())
        current_show = normalize(completed_item.get("show_title"))
        current_order = (
            int(completed_item.get("season") or 0),
            int(completed_item.get("episode") or 0),
        )
        candidates = []
        for row in rows:
            path = str(row.get("file") or "")
            if "plugin.video.umbrella" not in path.casefold():
                continue
            query = parse_qs(urlparse(path).query)
            metadata = {}
            try:
                raw_meta = query.get("meta", [""])[0]
                metadata = json.loads(raw_meta) if raw_meta else {}
            except (TypeError, ValueError):
                metadata = {}
            show_title = row.get("showtitle") or metadata.get("tvshowtitle") or ""
            season = int(row.get("season") or metadata.get("season") or 0)
            episode_number = int(row.get("episode") or metadata.get("episode") or 0)
            title = row.get("title") or metadata.get("title") or ""
            if not show_title or not title or normalize(show_title) != current_show:
                continue
            order = (season, episode_number)
            if order <= current_order:
                continue
            art = dict(row.get("art") or metadata.get("art") or {})
            identity = "%s|%s|%s|%s" % (normalize(show_title), season, episode_number, path)
            episode_id = -int(hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12], 16)
            show_id = -int(hashlib.sha256(normalize(show_title).encode("utf-8")).hexdigest()[:12], 16)
            candidates.append((
                order,
                show_id,
                {
                    "episodeid": episode_id,
                    "showtitle": show_title,
                    "title": title,
                    "season": season,
                    "episode": episode_number,
                    "file": path,
                    "art": art,
                },
            ))
        if not candidates:
            return None
        candidates.sort(key=lambda candidate: candidate[0])
        _, show_id, episode = candidates[0]
        return show_id, episode

    def _umbrella_catalog_next(self, completed_item):
        """Resolve the next unwatched episode from Umbrella without a Kodi library scan."""
        import re

        def normalize(value):
            return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())

        show_title = str(completed_item.get("show_title") or "").strip()
        current_show = normalize(show_title)
        if not current_show:
            return None
        metadata = dict(completed_item.get("metadata") or {})
        tmdb = str(metadata.get("tmdb") or "")
        imdb = str(metadata.get("imdb") or "")
        tvdb = str(metadata.get("tvdb") or "")
        if not (tmdb or imdb or tvdb):
            xbmc.log(
                "%s: Umbrella catalogue lookup skipped; playback item has no TMDb/IMDb/TVDB ID"
                % self.log_prefix,
                xbmc.LOGDEBUG,
            )
            return None

        year = str(completed_item.get("year") or "")
        current_season = int(completed_item.get("season") or 0)
        current_episode = int(completed_item.get("episode") or 0)
        show_id = -int(hashlib.sha256(current_show.encode("utf-8")).hexdigest()[:12], 16)
        show_meta = {
            "tvshowtitle": show_title,
            "year": year,
            "tmdb": tmdb,
            "imdb": imdb,
            "tvdb": tvdb,
            "mediatype": "tvshow",
        }
        common = {
            "tvshowtitle": show_title,
            "year": year,
            "imdb": imdb,
            "tmdb": tmdb,
            "tvdb": tvdb,
            "meta": json.dumps(show_meta, separators=(",", ":")),
        }
        plugin_root = "plugin://plugin.video.umbrella/"
        properties = [
            "title", "file", "art", "plot", "year", "season", "episode",
            "playcount", "premiered", "uniqueid",
        ]

        def get_directory(path, request_id):
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "Files.GetDirectory",
                "params": {
                    "directory": path,
                    "media": "files",
                    "properties": properties,
                    "limits": {"start": 0, "end": 1000},
                },
            }
            response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
            if "error" in response:
                raise RuntimeError(response["error"])
            return response.get("result", {}).get("files", [])

        def episode_candidates(rows, minimum_order):
            candidates = []
            for row in rows:
                path = str(row.get("file") or "")
                if "plugin.video.umbrella" not in path.casefold():
                    continue
                query = parse_qs(urlparse(path).query)
                try:
                    raw_meta = query.get("meta", [""])[0]
                    episode_meta = json.loads(raw_meta) if raw_meta else {}
                except (TypeError, ValueError):
                    episode_meta = {}
                title = row.get("title") or episode_meta.get("title") or ""
                episode_show = row.get("showtitle") or episode_meta.get("tvshowtitle") or show_title
                try:
                    season = int(row.get("season") or episode_meta.get("season") or 0)
                    number = int(row.get("episode") or episode_meta.get("episode") or 0)
                    playcount = int(row.get("playcount") or episode_meta.get("playcount") or 0)
                except (TypeError, ValueError):
                    continue
                order = (season, number)
                if (
                    not title
                    or normalize(episode_show) != current_show
                    or order <= minimum_order
                    or number <= 0
                    or str(episode_meta.get("unaired", "")).casefold() == "true"
                    or playcount > 0
                ):
                    continue
                candidates.append((order, row, episode_meta, path, title, episode_show))
            candidates.sort(key=lambda candidate: candidate[0])
            history = self.store.list_history(limit=500)
            for order, row, episode_meta, path, title, episode_show in candidates:
                already_completed = any(
                    normalize(previous.get("show_title")) == current_show
                    and int(previous.get("season") or 0) == order[0]
                    and int(previous.get("episode") or 0) == order[1]
                    for previous in history
                )
                if already_completed:
                    continue
                identity = "%s|%s|%s|%s" % (current_show, order[0], order[1], path)
                episode_id = -int(hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12], 16)
                art = dict(row.get("art") or episode_meta.get("art") or {})
                return {
                    "episodeid": episode_id,
                    "showtitle": episode_show,
                    "title": title,
                    "season": order[0],
                    "episode": order[1],
                    "file": path,
                    "art": art,
                }
            return None

        try:
            # Umbrella's seasons directory gives the exact seasons that exist;
            # query the current season first, then later seasons in order.
            seasons_url = plugin_root + "?" + urlencode({
                "action": "seasons",
                **common,
                "art": json.dumps(completed_item.get("art") or {}, separators=(",", ":")),
            })
            season_rows = get_directory(seasons_url, "kodihome-umbrella-seasons")
            seasons = {}
            for row in season_rows:
                season_path = str(row.get("file") or "")
                season_query = parse_qs(urlparse(season_path).query)
                try:
                    season_number = int(season_query.get("season", [""])[0])
                except (TypeError, ValueError):
                    label_match = re.search(r"season\s*(\d+)", str(row.get("label") or ""), re.I)
                    if not label_match:
                        continue
                    season_number = int(label_match.group(1))
                if season_number >= current_season and season_path:
                    seasons[season_number] = season_path

            if current_season not in seasons:
                seasons[current_season] = plugin_root + "?" + urlencode({
                    "action": "episodes",
                    **common,
                    "season": current_season,
                })
            ordered_seasons = [current_season] + sorted(
                season for season in seasons if season > current_season
            )
            for season_number in ordered_seasons:
                rows = get_directory(
                    seasons[season_number],
                    "kodihome-umbrella-episodes-%s" % season_number,
                )
                minimum_order = (
                    current_season,
                    current_episode,
                ) if season_number == current_season else (season_number, 0)
                episode = episode_candidates(rows, minimum_order)
                if episode:
                    return show_id, episode
        except Exception as exc:
            xbmc.log(
                "%s: Umbrella catalogue lookup failed for %s: %s"
                % (self.log_prefix, show_title, exc),
                xbmc.LOGWARNING,
            )
        return None

    def _refresh_up_next(self, completed_item):
        """Prefer a queued episode, then the library, then Umbrella's catalogue."""
        queued = self._umbrella_queued_next(completed_item)
        if queued:
            self.store.set_up_next(queued[0], completed_item["item_key"], queued[1])
            return
        show_db_id = completed_item.get("tvshow_db_id") or self._resolve_tvshow_db_id(
            completed_item.get("show_title")
        )
        if show_db_id:
            request = {
                "jsonrpc": "2.0",
                "id": "kodihome-up-next",
                "method": "VideoLibrary.GetEpisodes",
                "params": {
                    "tvshowid": show_db_id,
                    "properties": [
                        "episodeid", "title", "showtitle", "season", "episode",
                        "playcount", "file", "art",
                    ],
                    "limits": {"start": 0, "end": 500},
                },
            }
            try:
                response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
                if "error" in response:
                    raise RuntimeError(response["error"])
                episodes = response.get("result", {}).get("episodes", [])
                current_order = (
                    int(completed_item.get("season") or 0),
                    int(completed_item.get("episode") or 0),
                )
                candidates = [
                    episode for episode in episodes
                    if episode.get("episodeid")
                    and (
                        int(episode.get("season") or 0),
                        int(episode.get("episode") or 0),
                    ) > current_order
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
                    "%s: could not refresh Kodi-library Up Next: %s"
                    % (self.log_prefix, exc),
                    xbmc.LOGWARNING,
                )

        catalog_next = self._umbrella_catalog_next(completed_item)
        if catalog_next:
            self.store.set_up_next(
                catalog_next[0], completed_item["item_key"], catalog_next[1]
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
            show_title = tag.getTVShowTitle() or xbmc.getInfoLabel("VideoPlayer.TVShowTitle") or ""
            season = int(tag.getSeason() or 0)
            episode = int(tag.getEpisode() or 0)
            if media_type not in ("movie", "episode"):
                if show_title and season >= 0 and episode >= 0:
                    media_type = "episode"
                else:
                    return None
            if not file_path:
                return None

            kodi_db_id = int(tag.getDbId() or 0) or None
            tvshow_db_id = (
                int(xbmc.getInfoLabel("VideoPlayer.TvShowDBID") or 0) or None
                if media_type == "episode"
                else None
            )
            if media_type == "episode" and not tvshow_db_id:
                tvshow_db_id = self._resolve_tvshow_id_from_episode(kodi_db_id)
            if media_type == "episode" and not tvshow_db_id:
                tvshow_db_id = self._resolve_tvshow_db_id(show_title)
            item_key = "%s:%s" % (media_type, kodi_db_id) if kodi_db_id else self._path_key(media_type, file_path)
            metadata = {}
            for unique_id in ("tmdb", "imdb", "tvdb"):
                try:
                    value = tag.getUniqueID(unique_id)
                    if value:
                        metadata[unique_id] = str(value)
                except Exception:
                    pass
            for key, method_name in (
                ("plot", "getPlot"),
                ("genre", "getGenres"),
                ("rating", "getRating"),
                ("premiered", "getPremiered"),
                ("mpaa", "getMpaa"),
                ("studio", "getStudios"),
                ("director", "getDirectors"),
                ("tagline", "getTagLine"),
                ("country", "getCountries"),
            ):
                try:
                    value = getattr(tag, method_name)()
                    if value not in (None, "", [], 0):
                        metadata[key] = value
                except Exception:
                    pass
            duration = max(0.0, float(self.getTotalTime()))
            current_time = max(0.0, float(self.getTime()))
            position = min(current_time, duration) if duration else current_time
            art = {}
            for art_key in ("thumb", "poster", "banner", "fanart", "clearart", "clearlogo", "landscape", "icon"):
                try:
                    art_value = list_item.getArt(art_key)
                    if art_value:
                        art[art_key] = art_value
                except Exception:
                    pass
            return {
                "item_key": item_key,
                "media_type": media_type,
                "kodi_db_id": kodi_db_id,
                "tvshow_db_id": tvshow_db_id,
                "title": tag.getTitle() or file_path.rsplit("/", 1)[-1],
                "show_title": show_title,
                "year": int(tag.getYear() or 0) or None,
                "season": season or None,
                "episode": episode or None,
                "file_path": file_path,
                "position_seconds": position,
                "duration_seconds": duration,
                "art": art,
                "metadata": metadata,
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
