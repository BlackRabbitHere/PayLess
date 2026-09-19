import logging
import time
from contextlib import ExitStack
from urllib.parse import urlsplit

from payment_scraper.config.settings import Settings
from payment_scraper.core.enums import ErrorCode, FetchMethod
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.fetcher import FetchResult, HttpFetcher
from payment_scraper.core.models import utc_now
from payment_scraper.core.url_policy import UrlPolicy

logger = logging.getLogger(__name__)


class BrowserFetcher:
    """Ordinary fresh Chromium context; native networking, no challenge interaction."""

    def __init__(self, settings: Settings, http: HttpFetcher):
        self.settings, self.http = settings, http

    def fetch(self, url: str, policy: UrlPolicy, access_check, selector: str | None) -> FetchResult:
        if not self.settings.playwright_enabled:
            raise ScraperError(ErrorCode.BROWSER_NAVIGATION_FAILED, "Chromium is disabled.")
        from playwright.sync_api import Error, TimeoutError, sync_playwright

        host = policy.validate(url)
        access_check(url)
        self.http.limiter.wait(host)
        started, start_time = time.monotonic(), utc_now()
        details = {"url": url, "host": host, "fetchMethod": "PLAYWRIGHT",
                   "startTime": start_time.isoformat(), "browserFallbackAttempted": True}
        chain, public_json = [], []
        try:
            with ExitStack() as stack:
                playwright = stack.enter_context(sync_playwright())
                browser = playwright.chromium.launch(headless=True)
                stack.callback(browser.close)
                context = browser.new_context(
                    service_workers="block", accept_downloads=False, ignore_https_errors=False,
                )
                stack.callback(context.close)
                page = context.new_page()
                stack.callback(page.close)
                requests_made = 0

                def guard(route):
                    nonlocal requests_made
                    request = route.request
                    requests_made += 1
                    try:
                        if request.is_navigation_request():
                            policy.validate(request.url)
                            if request.frame == page.main_frame:
                                if len(chain) > self.settings.max_redirects:
                                    raise ScraperError(ErrorCode.REDIRECT_LOOP, "Browser redirect limit.")
                                chain.append(request.url)
                        else:
                            resource_host = urlsplit(request.url).hostname
                            UrlPolicy(frozenset({resource_host})).validate(request.url)
                        if requests_made > self.settings.browser_max_requests:
                            route.abort()
                            return
                        route.continue_()
                    except ScraperError:
                        route.abort()

                context.route("**/*", guard)

                def capture(response):
                    if len(public_json) >= 10:
                        return
                    if (urlsplit(response.url).hostname in policy.domains
                            and response.request.resource_type in {"xhr", "fetch"}
                            and response.status == 200
                            and "application/json" in response.headers.get("content-type", "")):
                        try:
                            body = response.body()
                            if len(body) <= self.settings.max_response_bytes:
                                public_json.append((response.url, body.decode("utf-8")))
                        except Error:
                            pass

                page.on("response", capture)
                response = page.goto(
                    url, wait_until="domcontentloaded", timeout=self.settings.browser_navigation_timeout_ms,
                )
                if selector:
                    try:
                        page.wait_for_selector(
                            selector, state="attached", timeout=self.settings.browser_selector_timeout_ms,
                        )
                    except TimeoutError:
                        details["selectorMissing"] = selector
                page.wait_for_timeout(1500)
                policy.validate(page.url)
                body = page.content().encode("utf-8")
                if len(body) > self.settings.max_response_bytes:
                    raise ScraperError(ErrorCode.RESPONSE_TOO_LARGE, "Rendered page exceeded size limit.")
                status = response.status if response else 0
                content_type = (response.headers.get("content-type", "") if response else "").split(";")[0]
                result = FetchResult(
                    page.url, body, status, utc_now(), content_type=content_type,
                    method=FetchMethod.BROWSER, requested_url=url, redirect_chain=tuple(chain[:-1]),
                    duration_ms=int((time.monotonic() - started) * 1000), title=page.title(),
                    public_json=tuple(public_json),
                )
                details.update(httpStatus=status, finalUrl=page.url, title=result.title,
                               responseBytes=len(body), contentType=content_type, redirectChain=chain)
                return result
        except ScraperError:
            raise
        except Error as exc:
            details["httpExceptionType"] = type(exc).__name__
            raise ScraperError(
                ErrorCode.BROWSER_NAVIGATION_FAILED, f"Chromium navigation failed: {str(exc)[:300]}",
            ) from exc
        finally:
            details.update(endTime=utc_now().isoformat(), durationMs=int((time.monotonic() - started) * 1000))
            logger.info("browser_completed", extra=details)
