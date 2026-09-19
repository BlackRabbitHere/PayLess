from datetime import timedelta
from decimal import Decimal

import pytest

from payment_scraper.core.normalizer import (
    normalize_bank,
    normalize_instrument,
    normalize_merchant,
    normalize_promo_code,
    normalize_provider,
    parse_currency,
    parse_date,
    parse_percentage,
)


@pytest.mark.parametrize(
    "source,expected",
    [("₹487.50", "487.50"), ("₹5,000", "5000.00"), ("INR 1,00,000.25", "100000.25"), ("0", "0.00")],
)
def test_currency(source, expected):
    assert parse_currency(source) == Decimal(expected)


@pytest.mark.parametrize("source", ["₹-1", "₹1.001", "₹50 or ₹100", "1,2,3", "NaN", "", "up to ₹500"])
def test_currency_rejects_ambiguous_or_invalid(source):
    with pytest.raises(ValueError):
        parse_currency(source)


def test_percent_and_identifiers():
    assert parse_percentage("2.5% Off") == Decimal("2.5")
    assert normalize_merchant(" Swiggy Money ") == "SWIGGY"
    assert normalize_provider("gyftr") == "GYFTR"
    assert normalize_bank("ICICI Bank Credit Cards") == "ICICI"
    assert normalize_instrument("ICICI Bank Credit Cards") == "CREDIT_CARD"
    assert normalize_promo_code(" MixedCase ") == "MixedCase"


@pytest.mark.parametrize("source", ["-1%", "101%", "up to 10%", "10% or 20%"])
def test_reject_bad_percentage(source):
    with pytest.raises(ValueError):
        parse_percentage(source)


def test_dates_are_utc_and_date_only_means_india_calendar_day():
    assert parse_date("2026-09-18").isoformat() == "2026-09-17T18:30:00+00:00"
    assert parse_date("18 September 2026", end_of_day=True).isoformat() == "2026-09-18T18:29:59.999999+00:00"
    assert parse_date("2026-09-18T16:30:00+05:30").utcoffset() == timedelta(0)
    with pytest.raises(ValueError):
        parse_date("2026-09-18T16:30:00")
    with pytest.raises(ValueError):
        parse_date("09/10/2026")
