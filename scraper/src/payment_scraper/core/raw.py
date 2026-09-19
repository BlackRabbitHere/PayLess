from dataclasses import dataclass, field
from datetime import datetime

from payment_scraper.core.enums import (
    Availability,
    DiscountType,
    OfferType,
    ProviderId,
    StackingPolicy,
    TransactionMode,
)


@dataclass(frozen=True)
class ParseContext:
    provider: ProviderId
    merchant: str
    source_url: str
    scraped_at: datetime


@dataclass
class RawOffer:
    """Source values only. No numeric interpretation happens in selectors."""

    title: str
    offer_type: OfferType
    source_id: str | None = None
    transaction_mode: TransactionMode = TransactionMode.UNKNOWN
    face_value_text: str | None = None
    selling_price_text: str | None = None
    discount_text: str | None = None
    discount_type: DiscountType = DiscountType.UNKNOWN
    maximum_discount_text: str | None = None
    minimum_transaction_texts: list[str] = field(default_factory=list)
    issuers: list[str] = field(default_factory=list)
    instruments: list[str] = field(default_factory=list)
    promo_code: str | None = None
    valid_from_text: str | None = None
    valid_until_text: str | None = None
    usage_limit: str | None = None
    stacking_policy: StackingPolicy = StackingPolicy.UNKNOWN
    terms: list[str] = field(default_factory=list)
    action_url: str | None = None
    action_label: str | None = None
    availability: Availability = Availability.UNKNOWN
    warnings: list[str] = field(default_factory=list)
