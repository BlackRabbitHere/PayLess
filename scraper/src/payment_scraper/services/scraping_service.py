import hashlib
import json
import logging
import sqlite3
import threading
import time
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from payment_scraper.config.settings import Settings
from payment_scraper.core.blocked_page import reject_access_challenge
from payment_scraper.core.deduplicator import deduplicate, identify
from payment_scraper.core.enums import ErrorCode, FetchMethod, ScrapeStatus, VerificationStatus
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.fetcher import FetchResult, HttpFetcher
from payment_scraper.core.logging_config import scrape_context
from payment_scraper.core.models import ScrapeError, ScrapeMetadata, ScrapeResponse, ScrapeWarning, utc_now
from payment_scraper.core.normalizer import normalize_merchant, normalize_offer
from payment_scraper.core.observations import record_observations
from payment_scraper.core.raw import ParseContext
from payment_scraper.core.robots import SourceAccess
from payment_scraper.core.snapshot import SnapshotStore
from payment_scraper.core.url_policy import UrlPolicy
from payment_scraper.core.validator import verify_offer
from payment_scraper.providers.registry import ProviderRegistry, default_registry

logger = logging.getLogger(__name__)


class ScrapingService:
    def __init__(
        self,
        settings: Settings,
        registry: ProviderRegistry,
        fetcher,
        access,
        snapshots: SnapshotStore,
        browser=None,
        *,
        fixture=False,
    ):
        self.settings, self.registry, self.fetcher = settings, registry, fetcher
        self.access, self.snapshots, self.browser = access, snapshots, browser
        self.fixture = fixture
        # Session, robots state, browser and refresh are serialized within a worker.
        self._lock = threading.RLock()
        self.health = {}
        self.diagnostics = {}
        if not fixture:
            try:
                self.health = json.loads(
                    (settings.data_dir / "diagnostics" / "provider-health.json").read_text(encoding="utf-8")
                )
            except (OSError, ValueError):
                pass

    def close(self):
        self.fetcher.close()

    def scrape(self, provider: str, merchant: str, force_refresh: bool = False) -> ScrapeResponse:
        started = utc_now()
        tick = time.monotonic()
        response = ScrapeResponse(
            request_id=uuid4(),
            status=ScrapeStatus.FAILED,
            provider=provider.strip().upper(),
            merchant=merchant.strip().upper(),
            started_at=started,
            completed_at=started,
            metadata=ScrapeMetadata(fixture=self.fixture),
        )
        token = scrape_context.set(
            {
                "requestId": str(response.request_id),
                "provider": response.provider,
                "merchant": response.merchant,
            }
        )
        diagnostic = {"requestId": str(response.request_id), "provider": response.provider,
                      "merchant": response.merchant, "sources": [], "snapshots": [],
                      "browserFallbackAttempted": False}
        diagnostic["sourceHashes"] = {}
        self.diagnostics[str(response.request_id)] = diagnostic
        if self.fixture:
            response.warnings.append(
                ScrapeWarning(
                    code="FIXTURE_DATA", message="Synthetic fixture data; not a live commercial offer."
                )
            )
        try:
            with self._lock:
                adapter = self.registry.get(provider)
                try:
                    response.merchant = normalize_merchant(merchant)
                except ValueError as exc:
                    raise ScraperError(
                        ErrorCode.MERCHANT_NOT_SUPPORTED, "Merchant is not configured."
                    ) from exc
                if not adapter.supports(response.merchant):
                    raise ScraperError(
                        ErrorCode.MERCHANT_NOT_SUPPORTED, "Merchant is not configured for this provider."
                    )
                self.access.check_terms(adapter.config)
                collected, cache_hits = [], []
                for url in adapter.get_source_urls(response.merchant):
                    try:
                        offers, fetched = self._scrape_source(adapter, url, response, force_refresh)
                        cache_hits.append(fetched.cache_hit)
                        response.metadata.fetch_method = fetched.method
                        collected.extend(offers)
                    except ScraperError as exc:
                        logger.warning("source_failed", extra={"blockedReason": exc.code})
                        response.errors.append(
                            ScrapeError(
                                code=exc.code,
                                message=exc.message,
                                provider=response.provider,
                                retryable=exc.retryable,
                            )
                        )
                unique, duplicate_warnings = deduplicate(collected)
                response.warnings.extend(duplicate_warnings)
                response.metadata.offers_found = len(unique)
                response.metadata.cache_hit = bool(cache_hits) and all(cache_hits)
                response.offers = [
                    offer for offer in unique if offer.verification_status != VerificationStatus.INCOMPLETE
                ]
                response.metadata.offers_excluded = len(unique) - len(response.offers)
                if response.metadata.offers_excluded:
                    response.warnings.append(
                        ScrapeWarning(
                            code="INCOMPLETE_EXCLUDED",
                            message="Incomplete offers were excluded from import output.",
                        )
                    )
                if not response.offers and not response.errors:
                    response.errors.append(
                        ScrapeError(
                            code=ErrorCode.NO_OFFERS_FOUND,
                            provider=response.provider,
                            message="No complete offers could be extracted.",
                        )
                    )
                if response.offers:
                    uncertain = any(
                        o.verification_status != VerificationStatus.VERIFIED for o in response.offers
                    )
                    response.status = (
                        ScrapeStatus.PARTIAL
                        if (response.errors or uncertain or response.metadata.offers_excluded)
                        else ScrapeStatus.SUCCESS
                    )
        except ScraperError as exc:
            response.errors.append(
                ScrapeError(
                    code=exc.code, message=exc.message, provider=response.provider, retryable=exc.retryable
                )
            )
        except Exception:
            logger.exception("scrape_failed")
            response.errors.append(
                ScrapeError(
                    code=ErrorCode.INTERNAL_ERROR,
                    provider=response.provider,
                    message="An internal scraping error occurred.",
                )
            )
        finally:
            response.completed_at = utc_now()
            summary = {}
            for offer in response.offers:
                label = "DEMO" if self.fixture else offer.verification_status.value
                summary[label] = summary.get(label, 0) + 1
            if not response.offers:
                summary["FAILED"] = 1
            diagnostic.update(
                verificationSummary=summary, durationMs=int((time.monotonic() - tick) * 1000),
                offersFound=response.metadata.offers_found, offersExcluded=response.metadata.offers_excluded,
                cacheHit=response.metadata.cache_hit,
            )
            if not self.fixture:
                verified = bool(summary.get("VERIFIED")) and not any(
                    w.code == "SNAPSHOT_FAILED" for w in response.warnings
                )
                state = self.health.setdefault(response.provider, {})
                state.update(liveVerified=verified,
                             lastFailure=response.errors[-1].code.value if response.errors else None,
                             lastCheckedAt=response.completed_at.isoformat())
                if verified:
                    state["lastSuccessfulScrape"] = response.completed_at.isoformat()
                try:
                    folder = self.settings.data_dir / "diagnostics"
                    record_observations(self.settings.data_dir, response.offers, diagnostic["sourceHashes"])
                    folder.mkdir(parents=True, exist_ok=True)
                    (folder / f"{response.request_id}.json").write_text(
                        json.dumps(diagnostic, indent=2, default=str), encoding="utf-8",
                    )
                    (folder / "provider-health.json").write_text(
                        json.dumps(self.health, indent=2, default=str), encoding="utf-8",
                    )
                except (OSError, sqlite3.Error):
                    logger.exception("diagnostics_write_failed")
            while len(self.diagnostics) > 100:
                self.diagnostics.pop(next(iter(self.diagnostics)))
            logger.info(
                "scrape_completed",
                extra={
                    "durationMs": int((time.monotonic() - tick) * 1000),
                    "offersFound": len(response.offers),
                    "fetchMethod": response.metadata.fetch_method,
                    "cacheHit": response.metadata.cache_hit,
                    "offersExcluded": response.metadata.offers_excluded,
                    "verificationSummary": summary,
                    "browserFallbackAttempted": diagnostic["browserFallbackAttempted"],
                },
            )
            scrape_context.reset(token)
        return response

    def _scrape_source(self, adapter, url, response, force_refresh):
        policy = UrlPolicy(adapter.config.allowed_domains)

        def check(target):
            self.access.check(target, policy)

        diagnostic = self.diagnostics[str(response.request_id)]
        state = self.health.setdefault(response.provider, {})
        try:
            fetched = self.fetcher.fetch(url, policy, force_refresh=force_refresh, before_request=check)
            response.metadata.fetch_method = fetched.method
            self._snapshot(response, fetched)
            reject_access_challenge(fetched.html, fetched.status)
            state.update(httpReady=True, sourceReachable=True)
            if not adapter.has_offer_data(fetched.html):
                raise ScraperError(ErrorCode.JS_RENDER_REQUIRED, "Required offer structure absent from HTTP HTML.")
            diagnostic["sources"].append({"url": url, "method": "HTTP", "status": fetched.status})
        except ScraperError as exc:
            state["httpReady"] = False
            diagnostic["sources"].append({"url": url, "method": "HTTP", "failure": exc.code})
            if exc.result is not None:
                self._snapshot(response, exc.result)
            recoverable = {ErrorCode.READ_TIMEOUT, ErrorCode.FETCH_TIMEOUT, ErrorCode.BLOCK_PAGE,
                           ErrorCode.EMPTY_RESPONSE, ErrorCode.JS_RENDER_REQUIRED}
            if not (exc.code in recoverable and self.browser and self.settings.playwright_enabled
                    and adapter.config.browser_fallback):
                raise
            diagnostic["browserFallbackAttempted"] = True
            response.warnings.append(ScrapeWarning(
                code="HTTP_FALLBACK", message=f"HTTP {exc.code}; attempted ordinary Chromium navigation.",
            ))
            try:
                fetched = self.browser.fetch(url, policy, check, adapter.config.browser_selector)
                response.metadata.fetch_method = fetched.method
                self._snapshot(response, fetched)
                reject_access_challenge(fetched.html, fetched.status, browser=True)
                if fetched.status != 200:
                    code = {403: ErrorCode.HTTP_403, 404: ErrorCode.HTTP_404,
                            429: ErrorCode.HTTP_429}.get(
                                fetched.status, ErrorCode.HTTP_5XX if fetched.status >= 500
                                else ErrorCode.BROWSER_NAVIGATION_FAILED,
                            )
                    raise ScraperError(code, f"Browser received HTTP {fetched.status}.")
                state.update(browserReady=True, sourceReachable=True)
                diagnostic["sources"].append({"url": url, "method": "PLAYWRIGHT", "status": fetched.status})
            except ScraperError as browser_error:
                diagnostic["sources"].append({"url": url, "method": "PLAYWRIGHT", "failure": browser_error.code})
                raise
        context = ParseContext(adapter.config.provider, response.merchant, fetched.url, fetched.fetched_at)
        try:
            raw_offers = adapter.parse(fetched.html, context)
        except ScraperError:
            raise
        except Exception as exc:
            logger.exception("parser_failed")
            raise ScraperError(ErrorCode.PARSE_FAILED, "Provider HTML could not be parsed.") from exc
        if not raw_offers:
            raise ScraperError(ErrorCode.NO_OFFERS_FOUND, "No supported offers found in the public response.")
        offers = []
        for raw in raw_offers:
            try:
                offer, conflicts = normalize_offer(raw, context)
                policy.validate(str(offer.source_url), resolve=False)
                if offer.action_url:
                    policy.validate(str(offer.action_url), resolve=False)
                offer, warnings = verify_offer(offer, conflicts)
                offer = identify(offer, raw.source_id)
                offers.append(offer)
                response.warnings.extend(
                    ScrapeWarning(code="OFFER_SANITY", message=warning, external_key=offer.external_key)
                    for warning in warnings
                )
                logger.info("offer_validated", extra={"verificationStatus": offer.verification_status})
            except (ValueError, ValidationError, ScraperError):
                logger.warning("offer_validation_failed", exc_info=True)
                response.errors.append(
                    ScrapeError(
                        code=ErrorCode.VALIDATION_FAILED,
                        provider=response.provider,
                        message="A source offer failed canonical validation.",
                    )
                )
        return offers, fetched

    def _snapshot(self, response, fetched):
        self.diagnostics[str(response.request_id)]["sourceHashes"][fetched.url] = hashlib.sha256(
            fetched.body
        ).hexdigest()
        try:
            path = self.snapshots.save(response.provider, response.merchant, fetched)
            if path:
                self.diagnostics[str(response.request_id)]["snapshots"].append(str(path))
                logger.info("snapshot_saved", extra={"snapshotPath": str(path)})
        except OSError:
            logger.exception("snapshot_failed")
            response.warnings.append(
                ScrapeWarning(code="SNAPSHOT_FAILED", message="Raw snapshot could not be saved.")
            )


class FixtureFetcher:
    """Explicit offline injection. Never used as an automatic live-failure fallback."""

    def __init__(self, files: dict[str, Path]):
        self.files = files

    def fetch(self, url, policy, **kwargs):
        policy.validate(url, resolve=False)
        path = self.files.get(url)
        if path is None:
            raise ScraperError(ErrorCode.SOURCE_UNAVAILABLE, "No fixture configured for this source.")
        return FetchResult(url, path.read_bytes(), 200, utc_now(), method=FetchMethod.FIXTURE)

    def close(self):
        pass


class FixtureAccess:
    def check_terms(self, config):
        pass

    def check(self, url, policy):
        policy.validate(url, resolve=False)


def build_service(settings: Settings | None = None) -> ScrapingService:
    settings = settings or Settings.from_env()
    registry = default_registry()
    if settings.fixture_dir:
        # One synthetic fixture per merchant. Never repeat it under every live URL.
        for adapter in registry.all():
            adapter.config = replace(
                adapter.config, sources=adapter.config.fixture_sources or {
                    merchant: urls[:1] for merchant, urls in adapter.config.sources.items()
                }
            )
        files = {
            url: settings.fixture_dir / f"{p.config.provider.value.lower()}_{m.lower()}.html"
            for p in registry.all()
            for m in p.config.sources
            for url in p.get_source_urls(m)
        }
        return ScrapingService(
            settings, registry, FixtureFetcher(files), FixtureAccess(), SnapshotStore(settings), fixture=True
        )
    fetcher = HttpFetcher(settings)
    from payment_scraper.core.browser_fetcher import BrowserFetcher

    browser = BrowserFetcher(settings, fetcher) if settings.playwright_enabled else None
    return ScrapingService(
        settings, registry, fetcher, SourceAccess(settings, fetcher), SnapshotStore(settings), browser
    )
