"""Real Chromium and JS execution; controlled transport, not a live provider test."""

import sys
from contextlib import contextmanager
from unittest.mock import Mock

import pytest
from playwright import sync_api

from payment_scraper.config.settings import Settings
from payment_scraper.core.browser_fetcher import BrowserFetcher
from payment_scraper.core.enums import ErrorCode
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.url_policy import UrlPolicy

pytestmark = pytest.mark.browser
URL = "https://controlled.example/offer"


@pytest.mark.parametrize("navigation_fails", [False, True])
def test_real_chromium_render_and_cleanup(monkeypatch, navigation_fails):
    closed = set()
    visited = []
    original_manager = sync_api.sync_playwright

    @contextmanager
    def tracked_playwright():
        manager = original_manager()
        playwright = manager.__enter__()
        try:
            original_launch = playwright.chromium.launch

            def launch(**kwargs):
                browser = original_launch(**kwargs)
                browser.on("disconnected", lambda _: closed.add("browser"))
                original_context = browser.new_context

                def new_context(**options):
                    context = original_context(**options)
                    context.on("close", lambda _: closed.add("context"))
                    context.on("page", lambda page: page.on("close", lambda _: closed.add("page")))
                    native_route = context.route

                    def controlled_route(pattern, handler):
                        def serve(route):
                            visited.append(route.request.url)
                            assert route.request.url == URL
                            if navigation_fails:
                                route.abort()
                            else:
                                route.fulfill(status=200, content_type="text/html", body="""<!doctype html>
                                    <html><body><script>
                                    const node = document.createElement('main');
                                    node.id = 'rendered-offer';
                                    node.textContent = 'JavaScript executed in Chromium';
                                    document.body.append(node);
                                    </script></body></html>""")
                        native_route(pattern, serve)

                    monkeypatch.setattr(context, "route", controlled_route)
                    return context

                monkeypatch.setattr(browser, "new_context", new_context)
                return browser

            monkeypatch.setattr(playwright.chromium, "launch", launch)
            yield playwright
        finally:
            manager.__exit__(*sys.exc_info())
            closed.add("playwright")

    monkeypatch.setattr(sync_api, "sync_playwright", tracked_playwright)
    policy = UrlPolicy(
        frozenset({"controlled.example"}),
        resolver=lambda *a, **kw: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    checked = []
    http = Mock()
    browser = BrowserFetcher(Settings(playwright_enabled=True), http)
    if navigation_fails:
        with pytest.raises(ScraperError) as caught:
            browser.fetch(URL, policy, checked.append, "#rendered-offer")
        assert caught.value.code == ErrorCode.BROWSER_NAVIGATION_FAILED
    else:
        result = browser.fetch(URL, policy, checked.append, "#rendered-offer")
        assert result.method == "BROWSER"
        assert '<main id="rendered-offer">JavaScript executed in Chromium</main>' in result.html
    assert visited == [URL]
    assert checked
    assert closed == {"page", "context", "browser", "playwright"}
    http.fetch.assert_not_called()
