from typing import Any, Literal

from pydantic import Field

from payment_scraper.core.models import ContractModel, ScrapeError


class ScrapeRequest(ContractModel):
    provider: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    merchant: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_ -]*$")
    force_refresh: bool = False


class HealthResponse(ContractModel):
    status: Literal["ok"] = "ok"
    schema_version: Literal[1] = 1
    mode: Literal["live", "fixture"]


class ProviderInfo(ContractModel):
    provider: str
    merchants: list[str]
    browser_fallback: bool
    live_ready: bool
    terms_reviewed: bool
    enabled: bool = False
    http_ready: bool | None = None
    browser_ready: bool = False
    parser_ready: bool = True
    source_reachable: bool | None = None
    live_verified: bool = False
    last_successful_scrape: str | None = None
    last_failure: str | None = None
    last_checked_at: str | None = None


class ProvidersResponse(ContractModel):
    schema_version: Literal[1] = 1
    providers: list[ProviderInfo]


class OfferSchemaResponse(ContractModel):
    schema_version: Literal[1] = 1
    json_schema: dict[str, Any]


class ApiErrorResponse(ContractModel):
    schema_version: Literal[1] = 1
    errors: list[ScrapeError]
