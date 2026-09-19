from fastapi import APIRouter, Request, Response

from payment_scraper.api.schemas import (
    ApiErrorResponse,
    HealthResponse,
    OfferSchemaResponse,
    ProviderInfo,
    ProvidersResponse,
    ScrapeRequest,
)
from payment_scraper.core.enums import ErrorCode, ScrapeStatus
from payment_scraper.core.models import ScrapedOffer, ScrapeResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request):
    return HealthResponse(mode="fixture" if request.app.state.service.fixture else "live")


@router.get("/api/v1/providers", response_model=ProvidersResponse)
def providers(request: Request):
    service = request.app.state.service
    reviewed = {v.strip().upper() for v in service.settings.terms_reviewed_providers.split(",")}
    return ProvidersResponse(
        providers=[
            ProviderInfo(
                provider=p.config.provider.value,
                merchants=sorted(p.config.sources),
                browser_fallback=p.config.browser_fallback,
                live_ready=service.health.get(p.config.provider.value, {}).get("liveVerified", False),
                terms_reviewed=p.config.provider.value in reviewed,
                enabled=getattr(service.settings, f"provider_{p.config.provider.value.lower()}_enabled"),
                browser_ready=bool(service.settings.playwright_enabled and p.config.browser_fallback),
                http_ready=service.health.get(p.config.provider.value, {}).get("httpReady"),
                source_reachable=service.health.get(p.config.provider.value, {}).get("sourceReachable"),
                live_verified=service.health.get(p.config.provider.value, {}).get("liveVerified", False),
                last_successful_scrape=service.health.get(p.config.provider.value, {}).get("lastSuccessfulScrape"),
                last_failure=service.health.get(p.config.provider.value, {}).get("lastFailure"),
                last_checked_at=service.health.get(p.config.provider.value, {}).get("lastCheckedAt"),
            )
            for p in service.registry.all()
        ]
    )


@router.post(
    "/api/v1/scrape",
    response_model=ScrapeResponse,
    responses={
        400: {"model": ScrapeResponse},
        422: {"model": ApiErrorResponse},
        500: {"model": ScrapeResponse | ApiErrorResponse},
        502: {"model": ScrapeResponse},
        503: {"model": ScrapeResponse},
    },
)
def scrape(body: ScrapeRequest, request: Request, response: Response):
    result = request.app.state.service.scrape(body.provider, body.merchant, body.force_refresh)
    if result.status == ScrapeStatus.FAILED:
        code = result.errors[0].code
        response.status_code = (
            500
            if code == ErrorCode.INTERNAL_ERROR
            else 400
            if code in {ErrorCode.PROVIDER_NOT_SUPPORTED, ErrorCode.MERCHANT_NOT_SUPPORTED}
            else 503
            if code
            in {
                ErrorCode.SOURCE_UNAVAILABLE,
                ErrorCode.ROBOTS_DISALLOWED,
                ErrorCode.FETCH_FORBIDDEN,
                ErrorCode.FETCH_RATE_LIMITED,
                ErrorCode.FETCH_TIMEOUT,
                ErrorCode.DNS_ERROR, ErrorCode.CONNECT_TIMEOUT, ErrorCode.READ_TIMEOUT,
                ErrorCode.TLS_ERROR, ErrorCode.HTTP_403, ErrorCode.HTTP_404,
                ErrorCode.HTTP_429, ErrorCode.HTTP_5XX, ErrorCode.BLOCK_PAGE,
                ErrorCode.BROWSER_BLOCK_PAGE, ErrorCode.BROWSER_NAVIGATION_FAILED,
                ErrorCode.PROVIDER_DISABLED,
            }
            else 502
        )
    return result


@router.get("/api/v1/schema/offers", response_model=OfferSchemaResponse)
def offer_schema():
    return OfferSchemaResponse(
        json_schema=ScrapedOffer.model_json_schema(by_alias=True, mode="serialization")
    )


@router.get("/api/v1/offers", response_model=list[ScrapeResponse],
            responses={422: {"model": ApiErrorResponse}, 500: {"model": ApiErrorResponse}})
def offers(request: Request, provider: str | None = None, merchant: str | None = None,
           force_refresh: bool = False):
    """Independent result envelopes preserve successful providers alongside source failures."""
    service = request.app.state.service
    adapters = service.registry.all()
    if provider:
        adapters = [p for p in adapters if p.config.provider.value == provider.upper()]
        if not adapters:
            return [service.scrape(provider, merchant or "", force_refresh)]
    return [
        service.scrape(p.config.provider.value, m, force_refresh)
        for p in adapters for m in p.config.sources
        if (not merchant or merchant.upper() == m)
    ]
