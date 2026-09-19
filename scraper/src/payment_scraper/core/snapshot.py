import hashlib
import json
import re
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

from payment_scraper.config.settings import Settings
from payment_scraper.core.fetcher import FetchResult
from payment_scraper.core.logging_config import scrape_context


class SnapshotStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = threading.Lock()

    def save(self, provider: str, merchant: str, result: FetchResult) -> Path | None:
        if not self.settings.save_raw_html or result.cache_hit:
            return None
        if not all(re.fullmatch(r"[A-Za-z0-9_]+", value) for value in (provider, merchant)):
            raise ValueError("Unsafe snapshot path component.")
        with self._lock:
            folder = self.settings.data_dir / "raw" / provider.lower() / merchant.lower()
            folder.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256(result.body).hexdigest()
            stem = result.fetched_at.strftime("%Y%m%dT%H%M%S%fZ") + "_" + digest[:16]
            path = folder / f"{stem}.html"
            with path.open("xb") as output:
                output.write(result.body)
            path.with_suffix(".json").write_text(
                json.dumps(
                    {
                        "provider": provider,
                        "merchant": merchant,
                        "url": result.url,
                        "sourceUrl": result.url,
                        "requestId": scrape_context.get().get("requestId"),
                        "requestedUrl": result.requested_url or result.url,
                        "finalUrl": result.url,
                        "redirectChain": list(result.redirect_chain),
                        "contentType": result.content_type,
                        "encoding": result.encoding,
                        "responseBytes": len(result.body),
                        "durationMs": result.duration_ms,
                        "httpStatus": result.status,
                        "timestamp": result.fetched_at.isoformat(),
                        "contentHash": digest,
                        "fetchMethod": "PLAYWRIGHT" if result.method.value == "BROWSER" else result.method.value,
                        "title": result.title,
                        "publicJsonResponses": [
                            {"url": url, "body": body} for url, body in result.public_json
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            self.prune()
            return path

    def prune(self):
        root = (self.settings.data_dir / "raw").resolve()
        cutoff = (datetime.now(UTC) - timedelta(days=self.settings.raw_html_retention_days)).timestamp()
        files = sorted(root.rglob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
        for index, path in enumerate(files):
            if index >= self.settings.snapshot_max_files or path.stat().st_mtime < cutoff:
                if path.is_symlink() or not path.resolve().is_relative_to(root):
                    continue
                path.unlink(missing_ok=True)
                metadata = path.with_suffix(".json")
                if not metadata.is_symlink() and metadata.resolve().is_relative_to(root):
                    metadata.unlink(missing_ok=True)
