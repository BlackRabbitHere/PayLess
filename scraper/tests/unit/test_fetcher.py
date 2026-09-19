from unittest.mock import Mock

import pytest
import requests

from payment_scraper.config.settings import Settings
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.fetcher import FetchResult, HttpFetcher, RateLimiter
from payment_scraper.core.models import utc_now
from payment_scraper.core.robots import SourceAccess
from payment_scraper.core.url_policy import UrlPolicy
from payment_scraper.providers.gyftr.config import CONFIG


def policy():
    return UrlPolicy(
        frozenset({"www.gyftr.com"}), resolver=lambda *a, **kw: [(2, 1, 6, "", ("8.8.8.8", 443))]
    )


def response(status=200, body=b"<html>offer</html>", headers=None):
    item = Mock()
    item.status_code = status
    item.headers = {"Content-Type": "text/html; charset=utf-8", **(headers or {})}
    item.encoding = "utf-8"
    item.iter_content.return_value = [body]
    item.__enter__ = Mock(return_value=item)
    item.__exit__ = Mock(return_value=None)
    return item


def fetcher(responses, **kwargs):
    session = requests.Session()
    session.get = Mock(side_effect=responses)
    settings = Settings(default_rate_limit_seconds=0, max_retries=2, **kwargs)
    sleeps = []
    instance = HttpFetcher(settings, session=session, sleep=sleeps.append)
    return instance, session, sleeps


def test_cache_force_refresh_tls_and_pool_reuse():
    instance, session, _ = fetcher([response(), response()])
    url = "https://www.gyftr.com/swiggy-money"
    assert not instance.fetch(url, policy()).cache_hit
    assert instance.fetch(url, policy()).cache_hit
    assert not instance.fetch(url, policy(), force_refresh=True).cache_hit
    assert session.get.call_count == 2
    assert session.get.call_args.kwargs["verify"] is True
    assert session.get.call_args.kwargs["allow_redirects"] is False
    assert session.trust_env is False


def test_transient_retry_after_and_bounded_retries():
    instance, session, sleeps = fetcher([response(429, headers={"Retry-After": "2"}), response()])
    instance.fetch("https://www.gyftr.com/x", policy())
    assert session.get.call_count == 2
    assert sleeps[0] >= 2
    instance, session, _ = fetcher([response(503), response(503), response(503)])
    with pytest.raises(ScraperError):
        instance.fetch("https://www.gyftr.com/x", policy())
    assert session.get.call_count == 3


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_permanent_errors_do_not_retry(status):
    instance, session, _ = fetcher([response(status)])
    with pytest.raises(ScraperError):
        instance.fetch("https://www.gyftr.com/x", policy())
    assert session.get.call_count == 1


def test_long_retry_after_stops_instead_of_retrying_early():
    instance, session, sleeps = fetcher([response(429, headers={"Retry-After": "3600"})])
    with pytest.raises(ScraperError) as caught:
        instance.fetch("https://www.gyftr.com/x", policy())
    assert caught.value.retryable
    assert not sleeps
    assert session.get.call_count == 1


@pytest.mark.parametrize(
    "target",
    [
        "http://www.gyftr.com/x",
        "https://evil.test/x",
        "https://127.0.0.1/x",
        "https://www.gyftr.com.evil.test/x",
        "https://u:p@www.gyftr.com/x",
        "https://www.gyftr.com:8000/x",
    ],
)
def test_ssrf_targets_and_redirects_rejected(target):
    instance, session, _ = fetcher([response(302, headers={"Location": target})])
    with pytest.raises(ScraperError) as caught:
        instance.fetch("https://www.gyftr.com/x", policy())
    assert caught.value.code == "URL_NOT_ALLOWED"
    assert session.get.call_count == 1


def test_private_dns_rejected():
    guard = UrlPolicy(
        frozenset({"www.gyftr.com"}), resolver=lambda *a, **kw: [(2, 1, 6, "", ("127.0.0.1", 443))]
    )
    with pytest.raises(ScraperError):
        guard.validate("https://www.gyftr.com/x")


def test_same_domain_redirect_checks_each_destination():
    instance, _, _ = fetcher([response(302, headers={"Location": "/new"}), response()])
    checked = []
    result = instance.fetch("https://www.gyftr.com/old", policy(), before_request=checked.append)
    assert result.url.endswith("/new")
    assert "https://www.gyftr.com/new" in checked


@pytest.mark.parametrize(
    "reply,expected",
    [
        (response(body=b"x" * 50), "RESPONSE_TOO_LARGE"),
        (response(headers={"Content-Type": "application/json"}), "UNSUPPORTED_CONTENT_TYPE"),
    ],
)
def test_response_limits(reply, expected):
    instance, _, _ = fetcher([reply], max_response_bytes=20)
    with pytest.raises(ScraperError) as caught:
        instance.fetch("https://www.gyftr.com/x", policy())
    assert caught.value.code == expected


def test_timeout_retry():
    instance, session, _ = fetcher([requests.Timeout(), response()])
    assert instance.fetch("https://www.gyftr.com/x", policy()).status == 200
    assert session.get.call_count == 2


def test_rate_limit_is_per_domain():
    now, sleeps = [100.0], []

    def sleep(duration):
        sleeps.append(duration)
        now[0] += duration

    limiter = RateLimiter(3, clock=lambda: now[0], sleep=sleep)
    limiter.wait("a")
    limiter.wait("b")
    limiter.wait("a")
    assert sleeps == [3]


def test_robots_deny_and_cache():
    transport = Mock()
    transport.fetch.return_value = FetchResult(
        "https://www.gyftr.com/robots.txt", b"User-agent: *\nDisallow: /private\n", 200, utc_now()
    )
    access = SourceAccess(Settings(save_raw_html=False), transport)
    access.check("https://www.gyftr.com/private", policy())
    assert access.metadata["https://www.gyftr.com/private"]["allowed"] is False
    access.check("https://www.gyftr.com/public", policy())
    assert transport.fetch.call_count == 1


def test_terms_review_is_not_activation():
    access = SourceAccess(Settings(), Mock())
    access.check_terms(CONFIG)
    access.settings.provider_gyftr_enabled = False
    with pytest.raises(ScraperError) as caught:
        access.check_terms(CONFIG)
    assert caught.value.code == "PROVIDER_DISABLED"


def test_expired_cache_fetches_again():
    instance, session, _ = fetcher([response(), response()], cache_ttl_seconds=1)
    now = [100.0]
    instance.clock = lambda: now[0]
    instance.fetch("https://www.gyftr.com/x", policy())
    now[0] += 2
    assert not instance.fetch("https://www.gyftr.com/x", policy()).cache_hit
    assert session.get.call_count == 2
