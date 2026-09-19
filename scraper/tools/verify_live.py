"""Bounded live CLI/API/browser evidence; never injects fixtures."""
import argparse
import hashlib
import json
import subprocess
import sys

from payment_scraper.config.settings import Settings
from payment_scraper.core.blocked_page import reject_access_challenge
from payment_scraper.core.browser_fetcher import BrowserFetcher
from payment_scraper.core.deduplicator import identify
from payment_scraper.core.fetcher import HttpFetcher
from payment_scraper.core.models import ScrapedOffer
from payment_scraper.core.normalizer import normalize_offer
from payment_scraper.core.raw import ParseContext
from payment_scraper.core.robots import SourceAccess
from payment_scraper.core.snapshot import SnapshotStore
from payment_scraper.core.url_policy import UrlPolicy
from payment_scraper.core.validator import verify_offer
from payment_scraper.providers.registry import default_registry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args()
    settings = Settings.from_env()
    assert not settings.fixture_dir
    folder = settings.data_dir / "verification"
    folder.mkdir(parents=True, exist_ok=True)
    if args.browser:
        adapter = default_registry().get("GYFTR")
        policy = UrlPolicy(adapter.config.allowed_domains)
        http = HttpFetcher(settings)
        try:
            access = SourceAccess(settings, http)
            access.check_terms(adapter.config)
            fetched = BrowserFetcher(settings, http).fetch(
                adapter.get_source_urls("SWIGGY")[0], policy,
                lambda url: access.check(url, policy), adapter.config.browser_selector,
            )
            snapshot = SnapshotStore(settings).save("GYFTR", "SWIGGY", fetched)
            reject_access_challenge(fetched.html, fetched.status, browser=True)
            assert fetched.status == 200
            context = ParseContext(adapter.config.provider, "SWIGGY", fetched.url, fetched.fetched_at)
            offers = [identify(verify_offer(*normalize_offer(raw, context))[0], raw.source_id)
                      for raw in adapter.parse(fetched.html, context)]
            assert offers and all(o.verification_status == "VERIFIED" for o in offers)
            output = {"fetchMethod": "PLAYWRIGHT", "status": fetched.status, "snapshot": str(snapshot),
                      "sourceHash": hashlib.sha256(fetched.body).hexdigest(),
                      "offers": [o.model_dump(mode="json", by_alias=True) for o in offers]}
            (folder / "browser_gyftr.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
            print(f"GYFTR Chromium: {len(offers)} verified offers; snapshot {snapshot}")
        finally:
            http.close()
        return
    for provider, merchant in (("yatra", "yatra"), ("gyftr", "swiggy"), ("easemytrip", "easemytrip")):
        command = [sys.executable, "-m", "payment_scraper.cli", "scrape", "--provider", provider,
                   "--merchant", merchant, "--force-refresh", "--json"]
        result = subprocess.run(command, capture_output=True, timeout=180)
        path = folder / f"live_{provider}_cli.json"
        path.write_bytes(result.stdout)
        (folder / f"live_{provider}_cli.log").write_bytes(result.stderr)
        data = json.loads(result.stdout)
        assert not data["metadata"]["fixture"]
        for offer in data["offers"]:
            ScrapedOffer.model_validate(offer)
        print(f"{provider}: exit={result.returncode} status={data['status']} offers={len(data['offers'])}")


if __name__ == "__main__":
    main()
