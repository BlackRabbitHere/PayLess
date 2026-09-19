"""Fetch configured offer sources through access gates and save real snapshots before parsing."""

import argparse
import json

from payment_scraper.config.settings import Settings
from payment_scraper.core.blocked_page import reject_access_challenge
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.fetcher import HttpFetcher
from payment_scraper.core.logging_config import configure_logging, scrape_context
from payment_scraper.core.robots import SourceAccess
from payment_scraper.core.snapshot import SnapshotStore
from payment_scraper.core.url_policy import UrlPolicy
from payment_scraper.providers.registry import default_registry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("yatra", "easemytrip", "gyftr"))
    parser.add_argument("--merchant", required=True)
    args = parser.parse_args()
    settings = Settings.from_env()
    if settings.fixture_dir:
        parser.error("Clear FIXTURE_DIR: this diagnostic requires live HTTP.")
    adapter = default_registry().get(args.provider)
    configure_logging(settings.log_level)
    token = scrape_context.set({"provider": adapter.config.provider, "merchant": args.merchant.upper()})
    http = HttpFetcher(settings)
    access = SourceAccess(settings, http)
    policy = UrlPolicy(adapter.config.allowed_domains)
    try:
        access.check_terms(adapter.config)
        urls = adapter.get_source_urls(args.merchant.upper())
        if not urls:
            parser.error("Merchant is not configured for this provider.")
        for url in urls:
            result = http.fetch(url, policy, force_refresh=True, before_request=lambda u: access.check(u, policy))
            reject_access_challenge(result.html, result.status)
            path = SnapshotStore(settings).save(adapter.config.provider, args.merchant.upper(), result)
            print(json.dumps({
                "fixture": False, "fetchMethod": result.method, "requestedUrl": url,
                "finalUrl": result.url, "status": result.status, "contentType": result.content_type,
                "responseBytes": len(result.body), "durationMs": result.duration_ms,
                "redirectChain": result.redirect_chain, "snapshot": str(path),
            }))
    except ScraperError as exc:
        print(json.dumps({"code": exc.code, "message": exc.message, "fixture": False}))
        return 1
    finally:
        http.close()
        scrape_context.reset(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
