"""Verify the scraper source and contract bytes recorded before relocation."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "data/scraper-freeze-manifest.json").read_text(encoding="utf-8-sig"))
# Keep the original snapshot immutable; explicitly audit only the Phase 5 observability edits.
overrides = json.loads((root / "data/scraper-phase5-overrides.json").read_text(encoding="utf-8"))
expected_overrides = {"src/payment_scraper/api/app.py", "src/payment_scraper/core/logging_config.py"}
if {entry["path"] for entry in overrides} != expected_overrides:
    raise SystemExit("Unexpected Phase 5 scraper override")
phase5 = {entry["path"]: entry["sha256"] for entry in overrides}
failures = []
for entry in manifest:
    path = root / "scraper" / entry["path"]
    content = path.read_bytes() if path.is_file() else b""
    # Git normalizes edited text on checkout; Phase 5 override hashes use LF.
    if entry["path"] in phase5:
        content = content.replace(b"\r\n", b"\n")
    if not path.is_file() or hashlib.sha256(content).hexdigest() != phase5.get(entry["path"], entry["sha256"]):
        failures.append(entry["path"])
if failures:
    raise SystemExit("Frozen scraper changed or missing: " + ", ".join(failures))
print(f"PASS: {len(manifest)} scraper files match the frozen baseline plus {len(phase5)} audited Phase 5 observability edits.")
