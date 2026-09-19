"""Freeze a sanitized, provenance-linked regression fixture from an existing live snapshot."""
import argparse
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup

from payment_scraper.core.models import ScrapedOffer

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("snapshot", type=Path)
parser.add_argument("--response", required=True, type=Path)
args = parser.parse_args()
raw = args.snapshot.read_bytes()
meta = json.loads(args.snapshot.with_suffix(".json").read_text(encoding="utf-8"))
response = json.loads(args.response.read_text(encoding="utf-8-sig"))
assert meta["fetchMethod"] in {"HTTP", "PLAYWRIGHT"} and meta["httpStatus"] == 200
assert hashlib.sha256(raw).hexdigest() == meta["contentHash"]
assert not response["metadata"]["fixture"] and response["offers"]
assert response["requestId"] == meta["requestId"]
for offer in response["offers"]:
    ScrapedOffer.model_validate(offer)
soup = BeautifulSoup(raw.decode(meta.get("encoding", "utf-8"), errors="replace"), "lxml")
for node in soup.select("script, form, input, iframe"):
    if node.name == "script" and (node.get("id") == "__NEXT_DATA__"
                                or node.get("type") == "application/ld+json"):
        continue
    node.decompose()
for node in soup.find_all(True):
    for key in list(node.attrs):
        if key.lower().startswith("on"):
            del node.attrs[key]
fixture = str(soup).encode("utf-8")
folder = Path("tests/fixtures/live")
folder.mkdir(parents=True, exist_ok=True)
path = folder / f"{meta['provider'].lower()}_{meta['merchant'].lower()}.html"
path.write_bytes(fixture)
provenance = {
    "capturedFromLive": True, "captureDate": meta["timestamp"], "provider": meta["provider"],
    "sourceUrl": meta["sourceUrl"], "sourceHash": meta["contentHash"],
    "hash": hashlib.sha256(fixture).hexdigest(), "rawSnapshot": str(args.snapshot),
    "fetchMethod": meta["fetchMethod"], "requestId": meta["requestId"],
    "sanitization": "Removed executable scripts, forms, input, iframe and event attributes.",
}
path.with_suffix(".json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
destination = Path("contracts")
destination.mkdir(exist_ok=True)
(destination / f"live_{meta['provider'].lower()}_example.json").write_text(
    json.dumps(response["offers"][0], indent=2, ensure_ascii=False), encoding="utf-8",
)
print(path)
