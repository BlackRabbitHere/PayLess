import sqlite3
from dataclasses import replace
from unittest.mock import Mock

import pytest
import requests
from fastapi.testclient import TestClient

from payment_scraper.api.app import create_app
from payment_scraper.config.settings import Settings
from payment_scraper.core.enums import ErrorCode, FetchMethod
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.fetcher import FetchResult, HttpFetcher
from payment_scraper.core.models import utc_now
from payment_scraper.core.observations import record_observations
from payment_scraper.core.robots import SourceAccess
from tests.unit.test_fetcher import policy, response


@pytest.mark.parametrize("failure,expected", [
    (requests.ConnectTimeout(), "CONNECT_TIMEOUT"),
    (requests.ReadTimeout(), "READ_TIMEOUT"),
    (requests.exceptions.SSLError(), "TLS_ERROR"),
    (response(body=b""), "EMPTY_RESPONSE"),
    (response(404), "HTTP_404"),
    (response(403), "HTTP_403"),
    (response(429), "HTTP_429"),
    (response(500), "HTTP_5XX"),
    (response(headers={"Content-Type": "image/png"}), "UNSUPPORTED_CONTENT_TYPE"),
])
def test_precise_fetch_diagnostics(failure, expected):
    session = requests.Session()
    session.get = Mock(side_effect=[failure])
    http = HttpFetcher(Settings(max_retries=0), session=session)
    with pytest.raises(ScraperError) as caught:
        http.fetch("https://www.gyftr.com/x", policy())
    assert caught.value.code == expected
    http.close()


def test_redirect_loop_is_bounded():
    session = requests.Session()
    session.get = Mock(return_value=response(302, headers={"Location": "/x"}))
    http = HttpFetcher(Settings(), session=session)
    with pytest.raises(ScraperError) as caught:
        http.fetch("https://www.gyftr.com/x", policy())
    assert caught.value.code == "REDIRECT_LOOP" and session.get.call_count == 1
    http.close()


def test_unavailable_robots_is_informational_and_cached():
    http = Mock()
    http.fetch.side_effect = ScraperError(ErrorCode.READ_TIMEOUT, "Robots timed out")
    access = SourceAccess(Settings(save_raw_html=False), http)
    access.check("https://www.gyftr.com/x", policy())
    access.check("https://www.gyftr.com/y", policy())
    assert http.fetch.call_count == 1
    assert access.metadata["https://www.gyftr.com"]["informationalOnly"]


def test_http_read_timeout_uses_browser_once(service, fixture_html):
    service.fetcher = Mock()
    service.fetcher.fetch.side_effect = ScraperError(ErrorCode.READ_TIMEOUT, "Read timed out")
    service.browser = Mock()
    service.browser.fetch.return_value = FetchResult(
        "https://www.gyftr.com/swiggy-gv", fixture_html.encode(), 200, utc_now(), method=FetchMethod.BROWSER,
    )
    result = service.scrape("GYFTR", "SWIGGY")
    assert result.offers and not result.errors
    service.browser.fetch.assert_called_once()
    assert service.diagnostics[str(result.request_id)]["browserFallbackAttempted"]


@pytest.mark.parametrize("code", ["HTTP_403", "HTTP_429", "TLS_ERROR", "DNS_ERROR"])
def test_permanent_failure_does_not_fallback(service, code):
    service.fetcher = Mock()
    service.fetcher.fetch.side_effect = ScraperError(ErrorCode(code), "Unavailable")
    service.browser = Mock()
    result = service.scrape("GYFTR", "SWIGGY")
    assert not result.offers and result.errors[0].code == code
    service.browser.fetch.assert_not_called()


def test_aggregate_keeps_other_providers_on_parser_failure(service):
    service.registry.get("YATRA").parse = Mock(side_effect=ValueError("Changed DOM"))
    with TestClient(create_app(service)) as client:
        result = client.get("/api/v1/offers")
        assert result.status_code == 200
        responses = {r["provider"]: r for r in result.json()}
        assert responses["YATRA"]["status"] == "FAILED"
        assert responses["GYFTR"]["offers"] and responses["EASEMYTRIP"]["offers"]
        health = client.get("/api/v1/providers").json()["providers"]
        assert not any(p["liveVerified"] for p in health)  # Fixtures never establish live health.


def test_aggregate_validation_matches_advertised_error_contract(service):
    with TestClient(create_app(service)) as client:
        reply = client.get("/api/v1/offers?force_refresh=not-a-boolean")
        assert reply.status_code == 422 and reply.json()["errors"][0]["code"] == "BAD_REQUEST"
        schema = client.get("/openapi.json").json()
        error_schema = schema["paths"]["/api/v1/offers"]["get"]["responses"]["422"]
        assert error_schema["content"]["application/json"]["schema"]["$ref"].endswith("/ApiErrorResponse")


def test_browser_snapshot_explicit_method(service, fixture_html):
    fetched = FetchResult("https://www.gyftr.com/swiggy-gv", fixture_html.encode(), 200,
                          utc_now(), method=FetchMethod.BROWSER)
    path = service.snapshots.save("GYFTR", "SWIGGY", fetched)
    assert '"fetchMethod": "PLAYWRIGHT"' in path.with_suffix(".json").read_text()


def test_bad_action_domain_is_excluded(service, fixture_html):
    adapter = service.registry.get("GYFTR")
    original = adapter.parse
    def unsafe(html, context):
        rows = original(html, context)
        return [replace(row, action_url="https://attacker.example/checkout") for row in rows]
    adapter.parse = unsafe
    result = service.scrape("GYFTR", "SWIGGY")
    assert not result.offers and result.errors[0].code == "VALIDATION_FAILED"


def test_observation_refresh_updates_one_identity(service, tmp_path):
    first = service.scrape("GYFTR", "SWIGGY").offers[0]
    record_observations(tmp_path, [first], {str(first.source_url): "a" * 64})
    second = first.model_copy(update={"scraped_at": first.scraped_at.replace(year=2027)})
    record_observations(tmp_path, [second], {str(first.source_url): "b" * 64})
    # A stale cached observation cannot replace the more recent observation.
    record_observations(tmp_path, [first], {str(first.source_url): "c" * 64})
    with sqlite3.connect(tmp_path / "observations.sqlite3") as db:
        rows = db.execute("SELECT first_seen_at,last_seen_at,source_hash FROM observations").fetchall()
    assert rows == [(first.scraped_at.isoformat(), second.scraped_at.isoformat(), "b" * 64)]
