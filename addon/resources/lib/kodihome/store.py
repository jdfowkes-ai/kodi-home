"""SQLite persistence for Kodi Home playback and personal lists."""

import json
import sqlite3
import time
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import xbmcaddon
import xbmcvfs


class LocalStore:
    """Own the add-on's local playback database."""

    def __init__(self, addon=None):
        self.addon = addon or xbmcaddon.Addon()
        profile = Path(xbmcvfs.translatePath(self.addon.getAddonInfo("profile")))
        profile.mkdir(parents=True, exist_ok=True)
        self.path = profile / "kodi-home.sqlite3"
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(str(self.path), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self):
        with self._connection() as connection:
            schema_version = connection.execute("PRAGMA user_version").fetchone()[0]
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS playback_progress (
                    item_key TEXT PRIMARY KEY,
                    media_type TEXT NOT NULL CHECK(media_type IN ('movie', 'episode')),
                    kodi_db_id INTEGER,
                    title TEXT NOT NULL,
                    show_title TEXT NOT NULL DEFAULT '',
                    year INTEGER,
                    season INTEGER,
                    episode INTEGER,
                    file_path TEXT NOT NULL,
                    position_seconds REAL NOT NULL DEFAULT 0,
                    duration_seconds REAL NOT NULL DEFAULT 0,
                    art_json TEXT NOT NULL DEFAULT '{}',
                    state TEXT NOT NULL DEFAULT 'in_progress'
                        CHECK(state IN ('in_progress', 'completed')),
                    updated_at INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_playback_progress_state_updated
                    ON playback_progress(state, updated_at DESC);

                CREATE TABLE IF NOT EXISTS watched_history (
                    playback_id TEXT PRIMARY KEY,
                    item_key TEXT NOT NULL,
                    media_type TEXT NOT NULL CHECK(media_type IN ('movie', 'episode')),
                    title TEXT NOT NULL,
                    show_title TEXT NOT NULL DEFAULT '',
                    year INTEGER,
                    season INTEGER,
                    episode INTEGER,
                    file_path TEXT NOT NULL,
                    duration_seconds REAL NOT NULL DEFAULT 0,
                    art_json TEXT NOT NULL DEFAULT '{}',
                    watched_at INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_watched_history_watched_at
                    ON watched_history(watched_at DESC);

                CREATE TABLE IF NOT EXISTS watchlist_items (
                    item_key TEXT PRIMARY KEY,
                    media_type TEXT NOT NULL CHECK(media_type IN ('movie', 'tvshow')),
                    kodi_db_id INTEGER,
                    title TEXT NOT NULL,
                    year INTEGER,
                    release_date TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    added_at INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_watchlist_items_release
                    ON watchlist_items(release_date, added_at DESC);

                CREATE TABLE IF NOT EXISTS app_groups (
                    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS apps (
                    package_name TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    icon_path TEXT NOT NULL DEFAULT '',
                    clearlogo_path TEXT NOT NULL DEFAULT '',
                    fanart_path TEXT NOT NULL DEFAULT '',
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS app_group_members (
                    group_id INTEGER NOT NULL,
                    package_name TEXT NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (group_id, package_name),
                    FOREIGN KEY (group_id) REFERENCES app_groups(group_id) ON DELETE CASCADE,
                    FOREIGN KEY (package_name) REFERENCES apps(package_name) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_app_group_members_order
                    ON app_group_members(group_id, sort_order);
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS up_next_items (
                    tvshow_db_id INTEGER PRIMARY KEY,
                    source_item_key TEXT NOT NULL,
                    episode_db_id INTEGER NOT NULL,
                    show_title TEXT NOT NULL DEFAULT '',
                    title TEXT NOT NULL,
                    season INTEGER,
                    episode INTEGER,
                    file_path TEXT NOT NULL,
                    art_json TEXT NOT NULL DEFAULT '{}',
                    updated_at INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS hidden_continue_watching (
                    item_key TEXT PRIMARY KEY,
                    hidden_at INTEGER NOT NULL
                )
                """
            )
            for table in ("playback_progress", "watched_history", "up_next_items"):
                columns = {
                    row["name"]
                    for row in connection.execute("PRAGMA table_info(%s)" % table)
                }
                if "art_json" not in columns:
                    connection.execute(
                        "ALTER TABLE %s ADD COLUMN art_json TEXT NOT NULL DEFAULT '{}'" % table
                    )
            if schema_version < 6 and connection.execute("SELECT COUNT(*) FROM app_groups").fetchone()[0] == 0:
                for sort_order, name in enumerate(("Favourites", "Kids", "Home Apps", "Gaming", "Music")):
                    connection.execute(
                        "INSERT OR IGNORE INTO app_groups (name, sort_order, created_at) VALUES (?, ?, ?)",
                        (name, sort_order, int(time.time())),
                    )
            connection.execute("PRAGMA user_version = 6")

    def save_progress(self, item):
        """Save the latest confirmed playback position for one item."""
        now = int(time.time())
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO playback_progress (
                    item_key, media_type, kodi_db_id, title, show_title, year,
                    season, episode, file_path, position_seconds,
                    duration_seconds, art_json, state, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?)
                ON CONFLICT(item_key) DO UPDATE SET
                    media_type=excluded.media_type,
                    kodi_db_id=excluded.kodi_db_id,
                    title=excluded.title,
                    show_title=excluded.show_title,
                    year=excluded.year,
                    season=excluded.season,
                    episode=excluded.episode,
                    file_path=excluded.file_path,
                    position_seconds=excluded.position_seconds,
                    duration_seconds=excluded.duration_seconds,
                    art_json=CASE WHEN excluded.art_json = '{}' THEN playback_progress.art_json ELSE excluded.art_json END,
                    state='in_progress',
                    updated_at=excluded.updated_at
                """,
                self._progress_values(item, now),
            )

    def mark_completed(self, item, playback_id):
        """Mark a naturally ended item complete and append one history entry."""
        now = int(time.time())
        values = self._progress_values(item, now)
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO playback_progress (
                    item_key, media_type, kodi_db_id, title, show_title, year,
                    season, episode, file_path, position_seconds,
                    duration_seconds, art_json, state, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
                ON CONFLICT(item_key) DO UPDATE SET
                    media_type=excluded.media_type,
                    kodi_db_id=excluded.kodi_db_id,
                    title=excluded.title,
                    show_title=excluded.show_title,
                    year=excluded.year,
                    season=excluded.season,
                    episode=excluded.episode,
                    file_path=excluded.file_path,
                    position_seconds=excluded.position_seconds,
                    duration_seconds=excluded.duration_seconds,
                    art_json=excluded.art_json,
                    state='completed',
                    updated_at=excluded.updated_at
                """,
                values,
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO watched_history (
                    playback_id, item_key, media_type, title, show_title, year,
                    season, episode, file_path, duration_seconds, art_json, watched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    playback_id,
                    item["item_key"],
                    item["media_type"],
                    item["title"],
                    item["show_title"],
                    item["year"],
                    item["season"],
                    item["episode"],
                    item["file_path"],
                    item["duration_seconds"],
                    json.dumps(item.get("art") or {}, sort_keys=True),
                    now,
                ),
            )

    def add_watchlist_item(self, item):
        """Add or refresh a locally managed movie or show watchlist entry.

        Required keys: item_key, media_type ('movie' or 'tvshow'), title.
        Optional keys: kodi_db_id, year, release_date (ISO YYYY-MM-DD),
        metadata (JSON-serializable dict of metadata/source identifiers).
        """
        media_type = item["media_type"]
        if media_type not in ("movie", "tvshow"):
            raise ValueError("Watchlist media_type must be 'movie' or 'tvshow'")
        metadata_json = json.dumps(item.get("metadata") or {}, sort_keys=True)
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO watchlist_items (
                    item_key, media_type, kodi_db_id, title, year,
                    release_date, metadata_json, added_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_key) DO UPDATE SET
                    media_type=excluded.media_type,
                    kodi_db_id=COALESCE(excluded.kodi_db_id, watchlist_items.kodi_db_id),
                    title=excluded.title,
                    year=COALESCE(excluded.year, watchlist_items.year),
                    release_date=COALESCE(excluded.release_date, watchlist_items.release_date),
                    metadata_json=CASE WHEN excluded.metadata_json = '{}' THEN watchlist_items.metadata_json ELSE excluded.metadata_json END
                """,
                (
                    item["item_key"],
                    media_type,
                    item.get("kodi_db_id"),
                    item["title"],
                    item.get("year"),
                    item.get("release_date"),
                    metadata_json,
                    int(time.time()),
                ),
            )

    def remove_watchlist_item(self, item_key):
        """Remove one entry explicitly by its stable local key."""
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM watchlist_items WHERE item_key = ?", (item_key,)
            )
            return cursor.rowcount > 0

    def remove_watchlist_for_playback(self, item):
        """Remove a movie or parent show after Kodi confirms AV playback."""
        with self._connection() as connection:
            if item["media_type"] == "movie":
                cursor = connection.execute(
                    """
                    DELETE FROM watchlist_items
                    WHERE item_key = ?
                       OR (kodi_db_id IS NOT NULL AND kodi_db_id = ? AND media_type = 'movie')
                    """,
                    (item["item_key"], item.get("kodi_db_id")),
                )
                return cursor.rowcount > 0

            if item["media_type"] == "episode":
                show_db_id = item.get("tvshow_db_id")
                if show_db_id:
                    cursor = connection.execute(
                        """
                        DELETE FROM watchlist_items
                        WHERE media_type = 'tvshow' AND kodi_db_id = ?
                        """,
                        (show_db_id,),
                    )
                    return cursor.rowcount > 0
                # A stable parent key can be supplied by a future metadata resolver.
                show_item_key = item.get("show_item_key")
                if show_item_key:
                    cursor = connection.execute(
                        """
                        DELETE FROM watchlist_items
                        WHERE media_type = 'tvshow' AND item_key = ?
                        """,
                        (show_item_key,),
                    )
                    return cursor.rowcount > 0
        return False

    def list_watchlist(self, bucket="all", today=None):
        """Return watchlist rows filtered as all, released, or unreleased.

        Missing release dates remain in the unreleased bucket until metadata is
        available; callers can refresh metadata without removing the entry.
        """
        if bucket not in ("all", "released", "unreleased"):
            raise ValueError("bucket must be 'all', 'released', or 'unreleased'")
        today = today or date.today().isoformat()
        if bucket == "released":
            query = """
                SELECT * FROM watchlist_items
                WHERE release_date IS NOT NULL AND release_date <= ?
                ORDER BY added_at DESC
            """
            params = (today,)
        elif bucket == "unreleased":
            query = """
                SELECT * FROM watchlist_items
                WHERE release_date IS NULL OR release_date > ?
                ORDER BY added_at DESC
            """
            params = (today,)
        else:
            query = "SELECT * FROM watchlist_items ORDER BY added_at DESC"
            params = ()
        with self._connection() as connection:
            rows = connection.execute(query, params).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item.pop("metadata_json"))
            result.append(item)
        return result

    def list_continue_watching(self, limit=100):
        """Return locally tracked items that have saved unfinished progress."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM playback_progress
                WHERE state = 'in_progress' AND position_seconds > 0
                  AND item_key NOT IN (SELECT item_key FROM hidden_continue_watching)
                ORDER BY updated_at DESC LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return self._decode_art_rows(rows)

    def remove_continue_watching(self, item_key):
        """Hide one item from Continue Watching without deleting its history."""
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO hidden_continue_watching (item_key, hidden_at)
                SELECT item_key, ? FROM playback_progress
                WHERE item_key = ? AND state = 'in_progress'
                """,
                (int(time.time()), item_key),
            )
            return cursor.rowcount > 0

    def show_continue_watching(self, item_key):
        """Make an item visible in Continue Watching after it starts again."""
        with self._connection() as connection:
            connection.execute(
                "DELETE FROM hidden_continue_watching WHERE item_key = ?",
                (item_key,),
            )

    def list_history(self, limit=100):
        """Return locally recorded natural playback completions."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM watched_history
                ORDER BY watched_at DESC LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return self._decode_art_rows(rows)

    def remove_history_entry(self, playback_id):
        """Delete one local History entry."""
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM watched_history WHERE playback_id = ?",
                (playback_id,),
            )
            return cursor.rowcount > 0

    def set_up_next(self, tvshow_db_id, source_item_key, episode):
        """Replace a show's Up Next target with its next eligible library episode."""
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO up_next_items (
                    tvshow_db_id, source_item_key, episode_db_id, show_title,
                    title, season, episode, file_path, art_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tvshow_db_id) DO UPDATE SET
                    source_item_key=excluded.source_item_key,
                    episode_db_id=excluded.episode_db_id,
                    show_title=excluded.show_title,
                    title=excluded.title,
                    season=excluded.season,
                    episode=excluded.episode,
                    file_path=excluded.file_path,
                    art_json=CASE WHEN excluded.art_json = '{}' THEN up_next_items.art_json ELSE excluded.art_json END,
                    updated_at=excluded.updated_at
                """,
                (
                    tvshow_db_id,
                    source_item_key,
                    episode["episodeid"],
                    episode.get("showtitle", ""),
                    episode.get("title", ""),
                    episode.get("season"),
                    episode.get("episode"),
                    episode.get("file", ""),
                    json.dumps(episode.get("art") or {}, sort_keys=True),
                    int(time.time()),
                ),
            )

    def clear_up_next(self, tvshow_db_id):
        """Remove a show's Up Next target when no eligible library episode exists."""
        with self._connection() as connection:
            connection.execute(
                "DELETE FROM up_next_items WHERE tvshow_db_id = ?",
                (tvshow_db_id,),
            )

    def list_up_next(self, limit=100):
        """Return each show's current locally selected next episode."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM up_next_items
                ORDER BY updated_at DESC LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return self._decode_art_rows(rows)

    def consume_up_next_episode(self, episode_db_id):
        """Remove an Up Next target once that exact episode starts playing."""
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM up_next_items WHERE episode_db_id = ?",
                (episode_db_id,),
            )
            return cursor.rowcount > 0

    def remove_up_next(self, tvshow_db_id):
        """Remove one show's Up Next entry."""
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM up_next_items WHERE tvshow_db_id = ?",
                (tvshow_db_id,),
            )
            return cursor.rowcount > 0

    def is_completed(self, item_key):
        """Return whether the local tracker has marked an item complete."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM playback_progress
                WHERE item_key = ? AND state = 'completed'
                """,
                (item_key,),
            ).fetchone()
        return row is not None

    def list_app_groups(self):
        """Return app groups with member counts, ordered for hub display."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT groups.group_id, groups.name, groups.sort_order,
                       COUNT(members.package_name) AS app_count
                FROM app_groups AS groups
                LEFT JOIN app_group_members AS members
                  ON members.group_id = groups.group_id
                GROUP BY groups.group_id
                ORDER BY groups.sort_order, groups.name COLLATE NOCASE
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_app_group(self, group_id):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT group_id, name, sort_order FROM app_groups WHERE group_id = ?",
                (int(group_id),),
            ).fetchone()
        return dict(row) if row else None

    def add_app_group(self, name):
        """Create a user-named app group and return its ID."""
        name = str(name or "").strip()
        if not name:
            raise ValueError("Group name is required")
        with self._connection() as connection:
            sort_order = connection.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM app_groups"
            ).fetchone()[0]
            cursor = connection.execute(
                "INSERT INTO app_groups (name, sort_order, created_at) VALUES (?, ?, ?)",
                (name, sort_order, int(time.time())),
            )
            return cursor.lastrowid

    def rename_app_group(self, group_id, name):
        name = str(name or "").strip()
        if not name:
            raise ValueError("Group name is required")
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE app_groups SET name = ? WHERE group_id = ?",
                (name, int(group_id)),
            )
            return cursor.rowcount > 0

    def remove_app_group(self, group_id):
        with self._connection() as connection:
            cursor = connection.execute(
                "DELETE FROM app_groups WHERE group_id = ?",
                (int(group_id),),
            )
            return cursor.rowcount > 0

    def list_apps(self, group_id=None):
        """Return app entries with artwork and optional group membership."""
        with self._connection() as connection:
            if group_id is None:
                rows = connection.execute(
                    """
                    SELECT package_name, title, icon_path, clearlogo_path, fanart_path
                    FROM apps ORDER BY title COLLATE NOCASE
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT apps.package_name, apps.title, apps.icon_path,
                           apps.clearlogo_path, apps.fanart_path,
                           members.sort_order
                    FROM apps
                    JOIN app_group_members AS members
                      ON members.package_name = apps.package_name
                    WHERE members.group_id = ?
                    ORDER BY members.sort_order, apps.title COLLATE NOCASE
                    """,
                    (int(group_id),),
                ).fetchall()
        return [dict(row) for row in rows]

    def add_app(self, package_name, title, icon_path="", group_id=None):
        """Save an installed Android app and optionally add it to one group."""
        package_name = str(package_name or "").strip()
        title = str(title or "").strip() or package_name
        if not package_name:
            raise ValueError("Android package name is required")
        icon_path = str(icon_path or "").strip()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO apps (package_name, title, icon_path, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(package_name) DO UPDATE SET
                    title = excluded.title,
                    icon_path = CASE WHEN excluded.icon_path = ''
                                     THEN apps.icon_path
                                     ELSE excluded.icon_path END
                """,
                (package_name, title, icon_path, int(time.time())),
            )
            if group_id is not None:
                group_id = int(group_id)
                sort_order = connection.execute(
                    "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM app_group_members WHERE group_id = ?",
                    (group_id,),
                ).fetchone()[0]
                connection.execute(
                    """
                    INSERT OR IGNORE INTO app_group_members
                        (group_id, package_name, sort_order)
                    VALUES (?, ?, ?)
                    """,
                    (group_id, package_name, sort_order),
                )
        return True

    def remove_app(self, package_name, group_id=None):
        """Remove an app from one group, or remove it from every group."""
        with self._connection() as connection:
            if group_id is not None:
                cursor = connection.execute(
                    "DELETE FROM app_group_members WHERE group_id = ? AND package_name = ?",
                    (int(group_id), str(package_name)),
                )
            else:
                cursor = connection.execute(
                    "DELETE FROM apps WHERE package_name = ?",
                    (str(package_name),),
                )
            return cursor.rowcount > 0

    def update_app_artwork(self, package_name, field, path):
        """Set a user-selected app logo or fanart path."""
        columns = {
            "icon": "icon_path",
            "clearlogo": "clearlogo_path",
            "fanart": "fanart_path",
        }
        column = columns.get(field)
        if not column:
            raise ValueError("Unsupported app artwork field")
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE apps SET %s = ? WHERE package_name = ?" % column,
                (str(path or ""), str(package_name)),
            )
            return cursor.rowcount > 0

    @staticmethod
    def _decode_art_rows(rows):
        result = []
        for row in rows:
            item = dict(row)
            try:
                item["art"] = json.loads(item.pop("art_json", "{}") or "{}")
            except (TypeError, ValueError):
                item["art"] = {}
            result.append(item)
        return result

    @staticmethod
    def _progress_values(item, updated_at):
        return (
            item["item_key"],
            item["media_type"],
            item["kodi_db_id"],
            item["title"],
            item["show_title"],
            item["year"],
            item["season"],
            item["episode"],
            item["file_path"],
            item["position_seconds"],
            item["duration_seconds"],
            json.dumps(item.get("art") or {}, sort_keys=True),
            updated_at,
        )
