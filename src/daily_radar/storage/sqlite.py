from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

from daily_radar.models import RadarItem


class RadarStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS items (
                  id TEXT PRIMARY KEY,
                  source TEXT NOT NULL,
                  category TEXT NOT NULL,
                  title TEXT NOT NULL,
                  url TEXT,
                  summary TEXT,
                  published_at TEXT,
                  fetched_at TEXT NOT NULL,
                  raw_json TEXT,
                  score REAL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS reports (
                  id TEXT PRIMARY KEY,
                  report_date TEXT NOT NULL,
                  markdown TEXT NOT NULL,
                  sent INTEGER DEFAULT 0,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def upsert_items(self, items: list[RadarItem]) -> None:
        with self.connect() as db:
            db.executemany(
                """
                INSERT INTO items(id, source, category, title, url, summary, published_at, fetched_at, raw_json, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  source=excluded.source,
                  category=excluded.category,
                  title=excluded.title,
                  url=excluded.url,
                  summary=excluded.summary,
                  published_at=excluded.published_at,
                  fetched_at=excluded.fetched_at,
                  raw_json=excluded.raw_json,
                  score=excluded.score
                """,
                [
                    (
                        item.id,
                        item.source,
                        item.category,
                        item.title,
                        item.url,
                        item.summary,
                        item.published_at,
                        item.fetched_at,
                        json.dumps(item.raw, ensure_ascii=False),
                        item.score,
                    )
                    for item in items
                ],
            )

    def list_items(self, limit: int = 100) -> list[RadarItem]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT id, source, category, title, url, summary, published_at, fetched_at, raw_json, score FROM items ORDER BY score DESC, fetched_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [RadarItem.from_row(tuple(r)) for r in rows]

    def save_report(self, report_date: str, markdown: str, sent: bool = False) -> str:
        rid = str(uuid.uuid4())
        with self.connect() as db:
            db.execute(
                "INSERT INTO reports(id, report_date, markdown, sent) VALUES (?, ?, ?, ?)",
                (rid, report_date, markdown, int(sent)),
            )
        return rid

    def list_reports(self, limit: int = 20) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
