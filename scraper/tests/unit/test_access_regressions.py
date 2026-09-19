import json
import socket
from dataclasses import replace
from unittest.mock import Mock

import pytest
import requests

from payment_scraper.config.settings import Settings
from payment_scraper.core.blocked_page import reject_access_challenge
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.fetcher import FetchResult, HttpFetcher, RateLimiter
from payment_scraper.core.models import utc_now
from payment_scraper.core.robots import ConservativeRobotsParser, SourceAccess
from payment_scraper.core.snapshot import SnapshotStore
from payment_scraper.providers.registry import default_registry
from tests.unit.test_fetcher import policy, response


def test_terms_activation_is_independent(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TERMS_REVIEWED_PROVIDERS", "yatra, EASEMYTRIP")
    settings = Settings.from_env()
    access = SourceAccess(settings, Mock())
    registry = default_registry()
    access.check_terms(registry.get("YATRA").config)
    access.check_terms(registry.get("EASEMYTRIP").config)
    access.check_terms(registry.get("GYFTR").config)
    settings.provider_gyftr_enabled = False
    with pytest.raises(ScraperError, match="configuration"):
        access.check_terms(registry.get("GYFTR").config)


def test_yatra_allow_root_does_not_override_narrow_disallow():
    parser = ConservativeRobotsParser()
    parser.parse(["User-agent: *", "Allow: /", "Disallow: /private", "Allow: /private/public"])
    assert not parser.can_fetch("PaymentRouteOptimizer/0.1", "https://www.gyftr.com/private")
    assert parser.can_fetch("PaymentRouteOptimizer/0.1", "https://www.gyftr.com/private/public")
    assert parser.can_fetch("PaymentRouteOptimizer/0.1", "https://www.gyftr.com/offers")


def test_matching_robots_groups_are_combined_and_unsupported_patterns_fail_closed():
    parser = ConservativeRobotsParser()
    parser.parse([
        "User-agent: *", "Allow: /", "", "User-agent: *", "Disallow: /private", "",
        "User-agent: PaymentRouteOptimizer", "Disallow: /*?secret=",
    ])
    assert not parser.can_fetch("AnotherBot", "https://www.gyftr.com/private")
    with pytest.raises(ScraperError, match="Unsupported robots pattern"):
        parser.can_fetch("PaymentRouteOptimizer/0.1", "https://www.gyftr.com/offer?secret=x")


@pytest.mark.parametrize("directive,allowed", [("Allow", True), ("Disallow", False)])
def test_universal_robots_wildcard(directive, allowed):
    parser = ConservativeRobotsParser()
    parser.parse(["User-agent: *", directive + ": *"])
    assert parser.can_fetch("PaymentRouteOptimizer/0.1", "https://www.gyftr.com/offer") is allowed


@pytest.mark.parametrize("title", [
    "Access Denied", "403 Forbidden", "Forbidden", "Captcha", "Just a moment...",
    "Bot verification", "Request blocked", "Unusual traffic", "Enable JavaScript",
])
def test_blocked_titles_cannot_be_parsed(title):
    with pytest.raises(ScraperError):
        reject_access_challenge(f"<html><title>{title}</title><main>Not an offer</main></html>")


def test_ordinary_terms_mentioning_captcha_or_javascript_are_not_a_challenge():
    reject_access_challenge("<h1>Card offer</h1><p>Enable JavaScript for booking; captcha may apply.</p>")


def test_real_fetcher_paces_consecutive_forced_refreshes_and_preserves_cache_time():
    now = [100.0]
    starts = []

    def sleep(seconds):
        now[0] += seconds

    def get(*args, **kwargs):
        starts.append(now[0])
        return response()

    session = requests.Session()
    session.get = get
    limiter = RateLimiter(3, clock=lambda: now[0], sleep=sleep)
    fetcher = HttpFetcher(Settings(), session=session, limiter=limiter, clock=lambda: now[0])
    url = "https://www.gyftr.com/x"
    try:
        first = fetcher.fetch(url, policy(), force_refresh=True)
        second = fetcher.fetch(url, policy(), force_refresh=True)
        cached = fetcher.fetch(url, policy())
        assert starts == [100.0, 103.0]
        assert not first.cache_hit and not second.cache_hit and cached.cache_hit
        assert cached.fetched_at == second.fetched_at
    finally:
        fetcher.close()


def test_snapshot_records_requested_url_redirect_and_response_details(tmp_path):
    result = FetchResult(
        "https://www.gyftr.com/final", b"<main>Public page</main>", 200, utc_now(),
        requested_url="https://www.gyftr.com/first",
        redirect_chain=("https://www.gyftr.com/first",), duration_ms=123,
    )
    path = SnapshotStore(Settings(data_dir=tmp_path)).save("GYFTR", "SWIGGY", result)
    data = json.loads(path.with_suffix(".json").read_text())
    assert data["requestedUrl"] == result.requested_url
    assert data["finalUrl"] == result.url
    assert data["redirectChain"] == [result.requested_url]
    assert data["responseBytes"] == len(result.body)
    assert data["durationMs"] == 123


@pytest.mark.parametrize("failure,expected", [
    (response(403), "HTTP_403"), (response(404), "HTTP_404"),
    (response(429), "HTTP_429"), (response(500), "HTTP_5XX"),
    (requests.Timeout(), "READ_TIMEOUT"), (requests.ConnectionError(), "SOURCE_UNAVAILABLE"),
])
def test_service_returns_structured_transport_failures(service, failure, expected, monkeypatch):
    session = requests.Session()
    session.get = Mock(side_effect=[failure])
    service.fetcher = HttpFetcher(Settings(max_retries=0), session=session)
    monkeypatch.setattr("payment_scraper.services.scraping_service.UrlPolicy", lambda _: policy())
    result = service.scrape("GYFTR", "SWIGGY", force_refresh=True)
    assert result.status == "FAILED" and result.offers == []
    assert result.errors[0].code == expected


def test_dns_failure_is_structured():
    guard = policy()
    guard.resolver = Mock(side_effect=socket.gaierror())
    with pytest.raises(ScraperError) as caught:
        guard.validate("https://www.gyftr.com/x")
    assert caught.value.code == "DNS_ERROR"


@pytest.mark.parametrize("kind,code", [
    ("malformed", "JS_RENDER_REQUIRED"), ("empty", "NO_OFFERS_FOUND"),
    ("exception", "PARSE_FAILED"), ("validation", "VALIDATION_FAILED"),
])
def test_service_returns_structured_parser_failures(service, fixture_html, context, kind, code):
    adapter = service.registry.get("GYFTR")
    service.fetcher = Mock()
    fetched = FetchResult(adapter.get_source_urls("SWIGGY")[0], fixture_html.encode(), 200, utc_now())
    service.fetcher.fetch.return_value = fetched
    if kind == "malformed":
        service.fetcher.fetch.return_value = replace(fetched, body=b"<html><p>broken")
    elif kind == "empty":
        adapter.parse = Mock(return_value=[])
    elif kind == "exception":
        adapter.parse = Mock(side_effect=ValueError("DOM changed"))
    else:
        raw = adapter.parse(fixture_html, context)[0]
        raw.selling_price_text = "not a monetary value"
        adapter.parse = Mock(return_value=[raw])
    result = service.scrape("GYFTR", "SWIGGY")
    assert result.errors[0].code == code
    assert not result.offers
