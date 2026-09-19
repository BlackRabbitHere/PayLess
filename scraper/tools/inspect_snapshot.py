"""Read a captured public response without making any network requests."""
import argparse
import json
from pathlib import Path

from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("provider")
parser.add_argument("--offset", type=int, default=-1)
args = parser.parse_args()
paths = sorted(p for p in Path("data/raw", args.provider).rglob("*.html")
               if "access_review" not in str(p))
path = paths[args.offset]
soup = BeautifulSoup(path.read_bytes(), "lxml")
print("SNAPSHOT", path)
print(soup.get_text(" ", strip=True)[:18000])
script = soup.select_one("#__NEXT_DATA__")
if script:
    state = json.loads(script.string).get("props", {}).get("pageProps", {}).get("reduxState", {})
    print("BRAND", json.dumps(state.get("brandInfo", {}), ensure_ascii=False)[:25000])
for script in soup.select('script[type="application/ld+json"]'):
    print("JSONLD", script.get_text()[:2000])
for node in soup.select("h1, h2, table")[:10]:
    print("NODE", str(node.parent)[:12000])
