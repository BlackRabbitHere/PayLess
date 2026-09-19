"""Observation history kept outside the canonical Spring offer schema."""
import sqlite3
from pathlib import Path


def record_observations(data_dir: Path, offers, source_hashes):
    data_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(data_dir / "observations.sqlite3") as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                external_key TEXT PRIMARY KEY, first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL, last_verified_at TEXT, source_hash TEXT,
                payload TEXT NOT NULL
            )
        """)
        for offer in offers:
            stamp = offer.scraped_at.isoformat()
            connection.execute("""
                INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(external_key) DO UPDATE SET
                    last_seen_at=excluded.last_seen_at,
                    last_verified_at=COALESCE(excluded.last_verified_at, observations.last_verified_at),
                    source_hash=COALESCE(excluded.source_hash, observations.source_hash),
                    payload=excluded.payload
                WHERE excluded.last_seen_at >= observations.last_seen_at
            """, (offer.external_key, stamp, stamp,
                  offer.last_verified_at.isoformat() if offer.last_verified_at else None,
                  source_hashes.get(str(offer.source_url)), offer.model_dump_json(by_alias=True)))
