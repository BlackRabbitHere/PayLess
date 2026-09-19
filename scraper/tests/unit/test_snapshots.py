import json
import os
from dataclasses import replace
from datetime import timedelta

from payment_scraper.config.settings import Settings
from payment_scraper.core.fetcher import FetchResult
from payment_scraper.core.models import utc_now
from payment_scraper.core.snapshot import SnapshotStore


def test_snapshot_metadata_retention_and_size_cap(tmp_path):
    store = SnapshotStore(Settings(data_dir=tmp_path, snapshot_max_files=2))
    now = utc_now()
    result = FetchResult("https://www.gyftr.com/x", b"<html>fixture</html>", 200, now)
    first = store.save("GYFTR", "SWIGGY", result)
    meta = json.loads(first.with_suffix(".json").read_text())
    assert meta["fetchMethod"] == "HTTP"
    assert len(meta["contentHash"]) == 64
    old = (now - timedelta(days=9)).timestamp()
    os.utime(first, (old, old))
    store.save("GYFTR", "SWIGGY", replace(result, fetched_at=now + timedelta(seconds=1)))
    assert not first.exists()
    assert not first.with_suffix(".json").exists()
    for i in range(2, 5):
        store.save("GYFTR", "SWIGGY", replace(result, fetched_at=now + timedelta(seconds=i)))
    assert len(list(tmp_path.rglob("*.html"))) == 2
