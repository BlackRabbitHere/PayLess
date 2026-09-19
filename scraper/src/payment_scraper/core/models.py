from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    HttpUrl,
    PlainSerializer,
    StringConstraints,
    model_validator,
)
from pydantic.alias_generators import to_camel

from payment_scraper.core.enums import (
    Availability,
    DiscountType,
    ErrorCode,
    FetchMethod,
    OfferType,
    ProviderId,
    ScrapeStatus,
    StackingPolicy,
    TransactionMode,
    VerificationStatus,
)


def no_float(value):
    if isinstance(value, (float, bool)):
        raise ValueError("Money must be a decimal string, integer or Decimal, never float.")
    return value


def decimal_string(value: Decimal) -> str:
    """Canonical scale: two places for whole/paise values, up to six for percentages."""
    whole, _, fraction = format(value, "f").partition(".")
    return whole + "." + fraction.rstrip("0").ljust(2, "0")


Money = Annotated[
    Decimal,
    BeforeValidator(no_float),
    Field(ge=0, max_digits=18, decimal_places=2),
    PlainSerializer(lambda v: format(v, ".2f"), return_type=str, when_used="json"),
]
Rate = Annotated[
    Decimal,
    BeforeValidator(no_float),
    Field(ge=0, max_digits=12, decimal_places=6),
    PlainSerializer(decimal_string, return_type=str, when_used="json"),
]
UtcTime = Annotated[AwareDatetime, AfterValidator(lambda v: v.astimezone(UTC))]
NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


def https_url(value: HttpUrl) -> HttpUrl:
    if value.scheme != "https" or value.username or value.password:
        raise ValueError("A public HTTPS URL without credentials is required.")
    return value


HttpsUrl = Annotated[HttpUrl, AfterValidator(https_url)]


class ContractModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class Voucher(ContractModel):
    face_value: Money | None = None
    selling_price: Money | None = None


class Discount(ContractModel):
    type: DiscountType = DiscountType.UNKNOWN
    value: Rate | None = None
    maximum_discount: Money | None = None

    @model_validator(mode="after")
    def percentage_bounds(self):
        if self.type == DiscountType.PERCENTAGE and self.value is not None and self.value > 100:
            raise ValueError("Percentage cannot exceed 100.")
        if self.type in (DiscountType.FLAT, DiscountType.CASHBACK) and self.value is not None:
            if self.value != self.value.quantize(Decimal(".01")):
                raise ValueError("A monetary discount cannot contain fractional paise.")
        return self


class ScrapedOffer(ContractModel):
    schema_version: Literal[1] = 1
    external_key: NonBlank
    provider: ProviderId
    merchant: NonBlank
    title: NonBlank
    offer_type: OfferType
    transaction_mode: TransactionMode = TransactionMode.UNKNOWN
    voucher: Voucher | None = None
    discount: Discount = Field(default_factory=Discount)
    minimum_transaction: Money | None = None
    eligible_issuers: list[NonBlank] = Field(default_factory=list)
    eligible_instrument_types: list[TransactionMode] = Field(default_factory=list)
    promo_code: NonBlank | None = None
    valid_from: UtcTime | None = None
    valid_until: UtcTime | None = None
    usage_limit: NonBlank | None = None
    stacking_policy: StackingPolicy = StackingPolicy.UNKNOWN
    terms: list[NonBlank] = Field(default_factory=list)
    availability: Availability = Availability.UNKNOWN
    source_url: HttpsUrl
    action_url: HttpsUrl | None = None
    action_label: NonBlank | None = None
    verification_status: VerificationStatus = VerificationStatus.INCOMPLETE
    last_verified_at: UtcTime | None = None
    scraped_at: UtcTime
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("validUntil cannot precede validFrom.")
        return self


class ScrapeError(ContractModel):
    code: ErrorCode
    message: str
    provider: str | None = None
    retryable: bool = False


class ScrapeWarning(ContractModel):
    code: str
    message: str
    external_key: str | None = None


class ScrapeMetadata(ContractModel):
    cache_hit: bool = False
    fetch_method: FetchMethod | None = None
    offers_found: int = 0
    offers_excluded: int = 0
    fixture: bool = False


class ScrapeResponse(ContractModel):
    schema_version: Literal[1] = 1
    request_id: UUID
    status: ScrapeStatus
    provider: str
    merchant: str
    started_at: UtcTime
    completed_at: UtcTime
    offers: list[ScrapedOffer] = Field(default_factory=list)
    warnings: list[ScrapeWarning] = Field(default_factory=list)
    errors: list[ScrapeError] = Field(default_factory=list)
    metadata: ScrapeMetadata = Field(default_factory=ScrapeMetadata)


def utc_now() -> datetime:
    return datetime.now(UTC)
