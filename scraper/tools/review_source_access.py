"""Fetch only curated public policy documents; never enable a provider or fetch offers."""

import argparse
import json

from bs4 import BeautifulSoup

from payment_scraper.config.settings import Settings
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.fetcher import HttpFetcher
from payment_scraper.core.logging_config import configure_logging
from payment_scraper.core.robots import SourceAccess
from payment_scraper.core.snapshot import SnapshotStore
from payment_scraper.core.url_policy import UrlPolicy
from payment_scraper.providers.registry import default_registry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("yatra", "easemytrip", "gyftr"), required=True)
    args = parser.parse_args()
    config = default_registry().get(args.provider).config
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    http = HttpFetcher(settings)
    access = SourceAccess(settings, http)
    policy = UrlPolicy(config.allowed_domains)
    snapshots = SnapshotStore(settings)
    urls = [config.terms_url]
    if args.provider == "yatra":
        urls.append("https://www.yatra.com/online/yatra-user-agreement.html")
    try:
        robots = http.fetch(
            "https://www." + args.provider + ".com/robots.txt", policy,
            allowed_types=("text/plain",), force_refresh=True,
        )
        path = snapshots.save(config.provider, "ACCESS_REVIEW", robots)
        print(json.dumps({"kind": "robots", "status": robots.status, "snapshot": str(path)}))
        for url in urls:
            result = http.fetch(url, policy, before_request=lambda u: access.check(u, policy))
            path = snapshots.save(config.provider, "ACCESS_REVIEW", result)
            soup = BeautifulSoup(result.html, "lxml")
            for node in soup.select("script, style, noscript"):
                node.decompose()
            visible = soup.get_text(" ", strip=True)
            print(json.dumps({
                "kind": "terms", "url": result.url, "status": result.status,
                "contentType": result.content_type, "bytes": len(result.body),
                "visibleTextLength": len(visible), "snapshot": str(path),
                "termsReviewComplete": False,
            }))
        for sources in config.sources.values():
            for url in sources:
                access.check(url, policy)
                print(json.dumps({
                    "robotsMetadata": access.metadata.get(url), "informationalOnly": True,
                    "sourceUrl": url, "offerFetched": False,
                }))
    except ScraperError as exc:
        print(json.dumps({"code": exc.code, "message": exc.message}))
        return 1
    finally:
        http.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
