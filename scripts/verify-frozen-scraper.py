"""Verify the scraper source and contract bytes recorded before relocation."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "data/scraper-freeze-manifest.json").read_text(encoding="utf-8-sig"))
failures = []
for entry in manifest:
    path = root / "scraper" / entry["path"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        failures.append(entry["path"])
if failures:
    raise SystemExit("Frozen scraper changed or missing: " + ", ".join(failures))
print(f"PASS: {len(manifest)} frozen scraper files match their original SHA-256 hashes.")
