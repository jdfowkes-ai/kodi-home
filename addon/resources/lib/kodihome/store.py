"""SQLite persistence for locally tracked Kodi playback."""

import sqlite3
import time
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

    def _initialize(self):
        with self._connect() as connection:
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
                    watched_at INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_watched_history_watched_at
                    ON watched_history(watched_at DESC);
                """
            )
            connection.execute("PRAGMA user_version = 1")

    def save_progress(self, item, playback_id):
        """Save the latest confirmed playback position for one item."""
        now = int(time.time())
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO playback_progress (
                    item_key, media_type, kodi_db_id, title, show_title, year,
                    season, episode, file_path, position_seconds,
                    duration_seconds, state, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?)
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
                    state='in_progress',
                    updated_at=excluded.updated_at
                """,
                self._progress_values(item, now),
            )

    def mark_completed(self, item, playback_id):
        """Mark a naturally ended item complete and append one history entry."""
        now = int(time.time())
        values = self._progress_values(item, now)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO playback_progress (
                    item_key, media_type, kodi_db_id, title, show_title, year,
                    season, episode, file_path, position_seconds,
                    duration_seconds, state, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
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
                    state='completed',
                    updated_at=excluded.updated_at
                """,
                values,
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO watched_history (
                    playback_id, item_key, media_type, title, show_title, year,
                    season, episode, file_path, duration_seconds, watched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    now,
                ),
            )

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
            updated_at,
        )
