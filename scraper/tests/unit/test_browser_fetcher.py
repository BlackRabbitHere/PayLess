from dataclasses import replace
from unittest.mock import Mock, patch

import pytest
from playwright.sync_api import Error

from payment_scraper.config.settings import Settings
from payment_scraper.core.browser_fetcher import BrowserFetcher
from payment_scraper.core.enums import FetchMethod
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.fetcher import FetchResult
from payment_scraper.core.models import utc_now


def test_browser_closes_every_resource_after_navigation_failure():
    settings = Settings(playwright_enabled=True)
    playwright, browser, context, page = Mock(), Mock(), Mock(), Mock()
    playwright.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page
    page.goto.side_effect = Error("navigation failed")
    manager = Mock(__enter__=Mock(return_value=playwright), __exit__=Mock(return_value=None))
    with patch("playwright.sync_api.sync_playwright", return_value=manager):
        with pytest.raises(ScraperError) as caught:
            BrowserFetcher(settings, Mock()).fetch("https://www.gyftr.com/x", Mock(), Mock(), ".offer")
    assert caught.value.code == "BROWSER_NAVIGATION_FAILED"
    page.close.assert_called_once()
    context.close.assert_called_once()
    browser.close.assert_called_once()
    assert browser.new_context.call_args.kwargs["ignore_https_errors"] is False


def test_http_200_challenge_tries_browser_once_and_preserves_browser_challenge(service):
    adapter = service.registry.get("GYFTR")
    adapter.config = replace(adapter.config, browser_fallback=True, browser_selector=".offer")
    service.settings.playwright_enabled = True
    service.fetcher = Mock()
    service.fetcher.fetch.return_value = FetchResult(
        "https://www.gyftr.com/x",
        b"<html><title>Just a moment...</title><form id='challenge-form'></form></html>",
        200,
        utc_now(),
    )
    service.browser = Mock()
    service.browser.fetch.return_value = replace(
        service.fetcher.fetch.return_value, method=FetchMethod.BROWSER,
    )
    result = service.scrape("GYFTR", "SWIGGY")
    assert result.errors[0].code == "BROWSER_BLOCK_PAGE"
    service.browser.fetch.assert_called_once()
