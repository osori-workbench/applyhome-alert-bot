from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Announcement


class AnnouncementStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sent_announcements (
                    dedupe_key TEXT PRIMARY KEY,
                    region TEXT NOT NULL,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    posted_on TEXT NOT NULL,
                    subscription_period TEXT NOT NULL,
                    sent_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def is_new(self, announcement: Announcement) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM sent_announcements WHERE dedupe_key = ?",
                (announcement.dedupe_key,),
            ).fetchone()
        return row is None

    def mark_sent(self, announcement: Announcement) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sent_announcements (
                    dedupe_key, region, category, name, posted_on, subscription_period
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    announcement.dedupe_key,
                    announcement.region,
                    announcement.category,
                    announcement.name,
                    announcement.posted_on,
                    announcement.subscription_period,
                ),
            )
