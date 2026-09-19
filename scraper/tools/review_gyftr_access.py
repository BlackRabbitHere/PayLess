"""Read only configured public access-policy pages using the production HTTP stack.

This diagnostic never marks terms reviewed and never fetches the offer source.
"""

import json

from bs4 import BeautifulSoup

from payment_scraper.config.settings import Settings
from payment_scraper.core.fetcher import HttpFetcher
from payment_scraper.core.logging_config import configure_logging
from payment_scraper.core.robots import SourceAccess
from payment_scraper.core.url_policy import UrlPolicy
from payment_scraper.providers.gyftr.config import CONFIG

settings = Settings.from_env()
configure_logging(settings.log_level)
fetcher = HttpFetcher(settings)
policy = UrlPolicy(CONFIG.allowed_domains)
access = SourceAccess(settings, fetcher)
try:
    access.check(CONFIG.terms_url, policy)
    result = fetcher.fetch(CONFIG.terms_url, policy, before_request=lambda url: access.check(url, policy))
    soup = BeautifulSoup(result.html, "lxml")
    for node in soup.select("script, style, noscript"):
        node.decompose()
    text = soup.get_text(" ", strip=True)
    print(
        json.dumps(
            {
                "httpStatus": result.status,
                "fetchMethod": result.method,
                "termsUrl": result.url,
                "visibleTextLength": len(text),
                "visibleTextExcerpt": text[:1000],
                "termsReviewComplete": False,
            },
            indent=2,
        )
    )
finally:
    fetcher.close()
