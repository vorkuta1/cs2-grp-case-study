from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class SqliteCache:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init(self) -> None:
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS fx_rates (
                    provider TEXT NOT NULL,
                    d TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (provider, d)
                )
                """
            )

    def put_fx_rates(self, provider: str, d: str, rates: dict[str, str]) -> None:
        payload = json.dumps(rates, sort_keys=True)
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO fx_rates(provider, d, payload) VALUES(?,?,?)",
                (provider, d, payload),
            )

    def get_latest_fx_rates(self, provider: str) -> tuple[str, dict[str, str]] | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT d, payload FROM fx_rates WHERE provider=? ORDER BY d DESC LIMIT 1",
                (provider,),
            ).fetchone()
        if row is None:
            return None
        d, payload = row
        return d, json.loads(payload)
