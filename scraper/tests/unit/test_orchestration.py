from dataclasses import replace
from unittest.mock import Mock

from payment_scraper.core.enums import ErrorCode, FetchMethod
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.fetcher import FetchResult
from payment_scraper.core.models import utc_now


def test_browser_only_for_missing_static_content_and_explicit_opt_in(service, fixture_html):
    adapter = service.registry.get("GYFTR")
    adapter.config = replace(adapter.config, browser_fallback=True, browser_selector="[data-voucher-id]")
    service.settings.playwright_enabled = True
    fetched = FetchResult(adapter.get_source_urls("SWIGGY")[0], b"<html>JS shell</html>", 200, utc_now())
    service.fetcher = Mock()
    service.fetcher.fetch.return_value = fetched
    service.browser = Mock()
    service.browser.fetch.return_value = replace(
        fetched, body=fixture_html.encode(), method=FetchMethod.BROWSER
    )
    assert service.scrape("GYFTR", "SWIGGY").status == "SUCCESS"
    service.browser.fetch.assert_called_once()
    service.browser.reset_mock()
    service.fetcher.fetch.return_value = replace(fetched, body=fixture_html.encode())
    assert service.scrape("GYFTR", "SWIGGY").status == "SUCCESS"
    service.browser.fetch.assert_not_called()


def test_forbidden_is_never_bypassed_with_browser(service):
    adapter = service.registry.get("GYFTR")
    adapter.config = replace(adapter.config, browser_fallback=True, browser_selector=".offer")
    service.settings.playwright_enabled = True
    service.fetcher = Mock()
    service.fetcher.fetch.side_effect = ScraperError(ErrorCode.FETCH_FORBIDDEN, "Denied")
    service.browser = Mock()
    result = service.scrape("GYFTR", "SWIGGY")
    assert result.errors[0].code == "FETCH_FORBIDDEN"
    service.browser.fetch.assert_not_called()


def test_missing_prices_excluded(service, fixture_html):
    service.fetcher = Mock()
    html = fixture_html.replace('<span data-field="selling-price">₹487.50</span>', "")
    service.fetcher.fetch.return_value = FetchResult(
        "https://www.gyftr.com/swiggy-money", html.encode(), 200, utc_now()
    )
    result = service.scrape("GYFTR", "SWIGGY")
    assert result.offers == []
    assert result.metadata.offers_excluded == 1
    assert result.errors[0].code == "NO_OFFERS_FOUND"
