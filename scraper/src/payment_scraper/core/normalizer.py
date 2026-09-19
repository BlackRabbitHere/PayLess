import re
from datetime import UTC, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from payment_scraper.core.enums import DiscountType, OfferType, ProviderId, TransactionMode
from payment_scraper.core.models import Discount, ScrapedOffer, Voucher
from payment_scraper.core.raw import ParseContext, RawOffer

_NUMBER = r"(?:\d{1,3}(?:,\d{2})*,\d{3}|\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def parse_currency(value: str) -> Decimal:
    cleaned = re.sub(r"^(?:₹|INR|Rs\.?)\s*", "", normalize_whitespace(value), flags=re.I)
    cleaned = re.sub(r"\s*(?:INR|/-)$", "", cleaned, flags=re.I)
    if not re.fullmatch(r"-?" + _NUMBER, cleaned):
        raise ValueError("Expected one unambiguous INR amount.")
    result = Decimal(cleaned.replace(",", ""))
    if result < 0 or result != result.quantize(Decimal(".01")):
        raise ValueError("Currency must be nonnegative with at most two decimal places.")
    return result.quantize(Decimal(".01"))


def parse_percentage(value: str) -> Decimal:
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%\s*(?:off|discount)?", value.strip(), re.I)
    if not match:
        raise ValueError("Expected one exact percentage, not an 'up to' range.")
    result = Decimal(match[1])
    if not 0 <= result <= 100:
        raise ValueError("Percentage outside 0..100.")
    return result


def parse_date(value: str, *, end_of_day: bool = False) -> datetime:
    """Date-only source terms mean an India calendar day; ambiguous numeric dates fail."""
    value = value.strip()
    if "T" in value:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("Timestamp needs an explicit timezone.")
        return result.astimezone(UTC)
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%d %b %Y"):
        try:
            day = datetime.strptime(value, fmt).date()
        except ValueError:
            continue
        clock = time(23, 59, 59, 999999) if end_of_day else time.min
        return datetime.combine(day, clock, ZoneInfo("Asia/Kolkata")).astimezone(UTC)
    raise ValueError("Unsupported or ambiguous date.")


def normalize_merchant(value: str) -> str:
    value = normalize_whitespace(value).upper().replace("-", "_").replace(" ", "_")
    value = {"SWIGGY_MONEY": "SWIGGY", "EASE_MY_TRIP": "EASEMYTRIP"}.get(value, value)
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_]{0,63}", value):
        raise ValueError("Invalid merchant identifier.")
    return value


def normalize_provider(value: str) -> ProviderId:
    return ProviderId(value.strip().upper())


def normalize_bank(value: str) -> str:
    value = normalize_whitespace(value).upper()
    for bank in ("ICICI", "HDFC", "SBI", "AXIS", "KOTAK", "IDFC", "INDUSIND"):
        if re.search(r"\b" + bank + r"\b", value):
            return bank
    return re.sub(r"\s+(BANK|CREDIT CARDS?|DEBIT CARDS?)\b", "", value).strip()


def normalize_instrument(value: str) -> TransactionMode:
    value = normalize_whitespace(value).upper().replace("_", " ")
    for phrase, mode in (
        ("CREDIT", "CREDIT_CARD"),
        ("DEBIT", "DEBIT_CARD"),
        ("UPI", "UPI"),
        ("EMI", "EMI"),
        ("NET BANKING", "NET_BANKING"),
        ("WALLET", "WALLET"),
        ("CARD", "CARD"),
    ):
        if phrase in value:
            return TransactionMode(mode)
    return TransactionMode.UNKNOWN


def normalize_promo_code(value: str | None) -> str | None:
    # Case can be significant; do not silently uppercase source codes.
    return value.strip() if value and value.strip() else None


def normalize_offer(raw: RawOffer, context: ParseContext) -> tuple[ScrapedOffer, list[str]]:
    def money(value):
        return parse_currency(value) if value is not None else None

    minima = {parse_currency(v) for v in raw.minimum_transaction_texts}
    warnings = list(raw.warnings)
    if len(minima) > 1:
        warnings.append("Conflicting minimum transaction requirements.")
    discount = None
    if raw.discount_text is not None:
        discount = (
            parse_percentage(raw.discount_text)
            if raw.discount_type == DiscountType.PERCENTAGE
            else money(raw.discount_text)
        )
    offer = ScrapedOffer(
        external_key="pending",
        content_hash="0" * 64,
        provider=context.provider,
        merchant=context.merchant,
        title=normalize_whitespace(raw.title),
        offer_type=raw.offer_type,
        transaction_mode=raw.transaction_mode,
        voucher=Voucher(face_value=money(raw.face_value_text), selling_price=money(raw.selling_price_text))
        if raw.offer_type == OfferType.VOUCHER_DISCOUNT
        else None,
        discount=Discount(
            type=raw.discount_type, value=discount, maximum_discount=money(raw.maximum_discount_text)
        ),
        minimum_transaction=next(iter(minima)) if len(minima) == 1 else None,
        eligible_issuers=sorted({normalize_bank(v) for v in raw.issuers}),
        eligible_instrument_types=sorted({normalize_instrument(v) for v in raw.instruments}),
        promo_code=normalize_promo_code(raw.promo_code),
        valid_from=parse_date(raw.valid_from_text) if raw.valid_from_text else None,
        valid_until=parse_date(raw.valid_until_text, end_of_day=True) if raw.valid_until_text else None,
        usage_limit=raw.usage_limit,
        stacking_policy=raw.stacking_policy,
        terms=[normalize_whitespace(v) for v in raw.terms if v.strip()],
        availability=raw.availability,
        source_url=context.source_url,
        action_url=raw.action_url,
        action_label=raw.action_label,
        scraped_at=context.scraped_at,
    )
    return offer, warnings
