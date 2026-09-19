import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Callable
from urllib.parse import urljoin

import requests
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from payment_scraper.config.settings import Settings
from payment_scraper.core.enums import ErrorCode, FetchMethod
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.url_policy import UrlPolicy

logger = logging.getLogger(__name__)
RETRY_STATUSES = {408, 429, 500, 502, 503, 504}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


@dataclass(frozen=True)
class FetchResult:
    url: str
    body: bytes
    status: int
    fetched_at: datetime
    content_type: str = "text/html"
    encoding: str = "utf-8"
    method: FetchMethod = FetchMethod.HTTP
    cache_hit: bool = False
    requested_url: str | None = None
    redirect_chain: tuple[str, ...] = ()
    duration_ms: int | None = None
    title: str | None = None
    public_json: tuple[tuple[str, str], ...] = ()

    @property
    def html(self) -> str:
        return self.body.decode(self.encoding, errors="replace")


class TemporaryFetchError(ScraperError):
    def __init__(self, code, message, retry_after: float | None = None):
        super().__init__(code, message, retryable=True)
        self.retry_after = retry_after


class RateLimiter:
    """One in-flight request globally; minimum interval per domain, including retries."""

    def __init__(self, interval: float, *, clock=time.monotonic, sleep=time.sleep):
        self.interval, self.clock, self.sleep = interval, clock, sleep
        self.next_request: dict[str, float] = {}
        self.delays: dict[str, float] = {}
        self.lock = threading.RLock()

    def set_delay(self, host: str, delay: float):
        with self.lock:
            self.delays[host] = max(self.delays.get(host, self.interval), delay)
            self.next_request[host] = max(self.next_request.get(host, 0), self.clock() + delay)

    def wait(self, host: str):
        with self.lock:
            delay = self.next_request.get(host, 0) - self.clock()
            if delay > 0:
                logger.info("rate_limit_wait", extra={"domain": host, "waitSeconds": round(delay, 3)})
                self.sleep(delay)
            self.next_request[host] = self.clock() + max(self.interval, self.delays.get(host, 0))


def retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        if value.strip().isdigit():
            return float(value)
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            date = date.replace(tzinfo=UTC)
        return max(0, (date - datetime.now(UTC)).total_seconds())
    except (ValueError, TypeError, OverflowError):
        return None


class HttpFetcher:
    def __init__(
        self, settings: Settings, *, session=None, limiter=None, clock=time.monotonic, sleep=time.sleep
    ):
        self.settings = settings
        self.session = session or requests.Session()
        # Never inherit proxy credentials, netrc authentication, or persistent login cookies.
        self.session.trust_env = False
        self.session.headers.update(
            {
                "User-Agent": settings.scraper_user_agent,
                "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-IN,en;q=0.9", "Connection": "keep-alive",
                # requests selects gzip/deflate and Brotli only when its decoder is installed.
                "Accept-Encoding": requests.utils.default_headers()["Accept-Encoding"],
            }
        )
        self.limiter = limiter or RateLimiter(settings.default_rate_limit_seconds)
        self.clock, self.sleep = clock, sleep
        self._lock = threading.RLock()
        self._cache: OrderedDict[tuple, tuple[float, FetchResult]] = OrderedDict()

    def close(self):
        self.session.close()

    def fetch(
        self,
        url: str,
        policy: UrlPolicy,
        *,
        force_refresh=False,
        allowed_types=("text/html", "application/xhtml+xml"),
        before_request: Callable[[str], None] | None = None,
        accepted_statuses=frozenset(),
    ) -> FetchResult:
        with self._lock:
            policy.validate(url)
            if before_request:
                before_request(url)
            key = (url, tuple(sorted(policy.domains)), tuple(allowed_types))
            cached = self._cache.get(key)
            if not force_refresh and cached and cached[0] > self.clock():
                self._cache.move_to_end(key)
                if before_request and cached[1].url != url:
                    before_request(cached[1].url)
                return replace(cached[1], cache_hit=True)
            result = self._fetch_redirects(url, policy, allowed_types, before_request, accepted_statuses)
            if result.status == 200 and self.settings.cache_ttl_seconds:
                self._cache[key] = (self.clock() + self.settings.cache_ttl_seconds, result)
                self._cache.move_to_end(key)
                while len(self._cache) > self.settings.cache_max_entries:
                    self._cache.popitem(last=False)
            return result

    def _fetch_redirects(self, url, policy, allowed_types, before_request, accepted_statuses):
        current = url
        started = self.clock()
        chain = []
        for redirect in range(self.settings.max_redirects + 1):
            policy.validate(current)
            if before_request:
                before_request(current)
            try:
                result = self._retry_request(current, policy, allowed_types, accepted_statuses)
            except ScraperError as exc:
                if exc.result is not None:
                    exc.result = replace(exc.result, requested_url=url, redirect_chain=tuple(chain))
                raise
            if isinstance(result, FetchResult):
                logger.info("fetch_completed", extra={
                    "url": url, "finalUrl": result.url, "redirectChain": chain,
                    "httpStatus": result.status, "contentType": result.content_type,
                    "responseBytes": len(result.body), "fetchMethod": result.method,
                    "durationMs": int((self.clock() - started) * 1000),
                })
                return replace(
                    result, requested_url=url, redirect_chain=tuple(chain),
                    duration_ms=int((self.clock() - started) * 1000),
                )
            if redirect == self.settings.max_redirects:
                raise ScraperError(ErrorCode.REDIRECT_LOOP, "Provider exceeded the redirect limit.")
            chain.append(current)
            current = urljoin(current, result)
            if current in chain:
                raise ScraperError(ErrorCode.REDIRECT_LOOP, "Provider redirected to an already visited URL.")
        raise AssertionError("Unreachable redirect state")

    def _retry_request(self, url, policy, allowed_types, accepted_statuses):
        jitter = wait_random_exponential(multiplier=1, max=self.settings.max_retry_wait_seconds)

        def wait(state):
            error = state.outcome.exception()
            return max(jitter(state), error.retry_after or 0)

        retrying = Retrying(
            stop=stop_after_attempt(self.settings.max_retries + 1),
            retry=retry_if_exception_type(TemporaryFetchError),
            wait=wait,
            sleep=self.sleep,
            reraise=True,
        )
        return retrying(self._request, url, policy, allowed_types, accepted_statuses)

    def _request(self, url, policy, allowed_types, accepted_statuses):
        host = policy.validate(url)
        self.limiter.wait(host)
        self.session.cookies.clear()
        started = self.clock()
        start_time = datetime.now(UTC)
        details = {"domain": host, "host": host, "url": url, "fetchMethod": "HTTP",
                   "startTime": start_time.isoformat(), "finalUrl": url, "httpStatus": None,
                   "contentType": None, "responseBytes": 0, "httpExceptionType": None}
        logger.info("request_started", extra=details)
        try:
            with self.session.get(
                url,
                timeout=(self.settings.http_connect_timeout, self.settings.http_read_timeout),
                allow_redirects=False,
                stream=True,
                verify=True,
            ) as response:
                status = response.status_code
                details["httpStatus"] = status
                logger.info(
                    "fetch",
                    extra={
                        "httpStatus": status,
                        "fetchMethod": "HTTP",
                        "durationMs": int((self.clock() - started) * 1000),
                    },
                )
                if status in REDIRECT_STATUSES:
                    location = response.headers.get("Location")
                    if not location:
                        raise ScraperError(ErrorCode.SOURCE_UNAVAILABLE, "Redirect has no destination.")
                    return location
                content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
                details["contentType"] = content_type
                declared = response.headers.get("Content-Length", "")
                if declared.isdigit() and int(declared) > self.settings.max_response_bytes:
                    raise ScraperError(
                        ErrorCode.RESPONSE_TOO_LARGE, "Provider response exceeded the size limit."
                    )
                chunks, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > self.settings.max_response_bytes:
                        raise ScraperError(
                            ErrorCode.RESPONSE_TOO_LARGE, "Provider response exceeded the size limit."
                        )
                    chunks.append(chunk)
                encoding = (
                    response.encoding
                    if "charset=" in response.headers.get("Content-Type", "").lower()
                    else "utf-8"
                )
                details["responseBytes"] = size
                result = FetchResult(
                    url, b"".join(chunks), status, datetime.now(UTC), content_type, encoding or "utf-8",
                    requested_url=url, duration_ms=int((self.clock() - started) * 1000),
                )
                try:
                    if status not in accepted_statuses:
                        self._check_status(status, response.headers.get("Retry-After"))
                        if not result.body.strip():
                            raise ScraperError(ErrorCode.EMPTY_RESPONSE, "Provider returned an empty body.")
                        if content_type not in allowed_types:
                            raise ScraperError(
                                ErrorCode.UNSUPPORTED_CONTENT_TYPE, "Unsupported response content type."
                            )
                except ScraperError as exc:
                    exc.result = result
                    raise
                return result
        except requests.exceptions.SSLError as exc:
            details["httpExceptionType"] = type(exc).__name__
            raise ScraperError(ErrorCode.TLS_ERROR, "Provider TLS validation failed.") from exc
        except requests.exceptions.ConnectTimeout as exc:
            details["httpExceptionType"] = type(exc).__name__
            raise TemporaryFetchError(ErrorCode.CONNECT_TIMEOUT, "Provider connection timed out.") from exc
        except requests.exceptions.Timeout as exc:
            details["httpExceptionType"] = type(exc).__name__
            raise TemporaryFetchError(
                ErrorCode.READ_TIMEOUT, "Provider response timed out."
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            details["httpExceptionType"] = type(exc).__name__
            message = str(exc).lower()
            code = (ErrorCode.READ_TIMEOUT if "read timed out" in message else
                    ErrorCode.DNS_ERROR if "name resolution" in message or "getaddrinfo" in message else
                    ErrorCode.SOURCE_UNAVAILABLE)
            raise TemporaryFetchError(code, "Provider connection failed.") from exc
        except requests.exceptions.RequestException as exc:
            details["httpExceptionType"] = type(exc).__name__
            raise ScraperError(ErrorCode.SOURCE_UNAVAILABLE, "Provider request failed.") from exc
        finally:
            details.update(endTime=datetime.now(UTC).isoformat(),
                           durationMs=int((self.clock() - started) * 1000))
            logger.info("request_completed", extra=details)
            self.session.cookies.clear()

    def _check_status(self, status: int, retry_after: str | None):
        if status in RETRY_STATUSES:
            code = ErrorCode.HTTP_429 if status == 429 else ErrorCode.HTTP_5XX
            delay = retry_after_seconds(retry_after)
            if delay is not None and delay > self.settings.max_retry_wait_seconds:
                # Stop now instead of retrying earlier than the provider permits.
                raise ScraperError(
                    code, "Provider requested a longer retry delay; retry later.", retryable=True
                )
            raise TemporaryFetchError(code, "Provider is temporarily unavailable.", delay)
        if status in (401, 403):
            raise ScraperError(ErrorCode.HTTP_403, f"Provider denied public access (HTTP {status}).")
        if status == 404:
            raise ScraperError(ErrorCode.HTTP_404, "Provider page was not found.")
        if status >= 500:
            raise ScraperError(ErrorCode.HTTP_5XX, f"Provider returned HTTP {status}.", retryable=True)
        if status != 200:
            raise ScraperError(ErrorCode.SOURCE_UNAVAILABLE, f"Provider returned HTTP {status}.")
