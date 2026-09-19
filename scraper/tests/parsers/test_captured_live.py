"""Offline regressions from genuine, sanitized public responses (not live checks)."""
import hashlib
import json
from dataclasses import replace
from datetime import datetime
from decimal import Decimal

import pytest

from payment_scraper.core.deduplicator import identify
from payment_scraper.core.models import ScrapedOffer
from payment_scraper.core.normalizer import normalize_offer
from payment_scraper.core.raw import ParseContext
from payment_scraper.core.validator import verify_offer
from payment_scraper.providers.registry import default_registry
from tests.conftest import FIXTURES


def captured(provider, merchant):
    path = FIXTURES / "live" / f"{provider}_{merchant}.html"
    meta = json.loads(path.with_suffix(".json").read_text())
    assert meta["capturedFromLive"] and hashlib.sha256(path.read_bytes()).hexdigest() == meta["hash"]
    adapter = default_registry().get(provider)
    context = ParseContext(adapter.config.provider, merchant.upper(), meta["sourceUrl"],
                           datetime.fromisoformat(meta["captureDate"]))
    return adapter, path.read_text(encoding="utf-8"), context


def normalized(adapter, html, context):
    assert adapter.has_offer_data(html)
    return [identify(verify_offer(*normalize_offer(raw, context))[0], raw.source_id)
            for raw in adapter.parse(html, context)]


@pytest.mark.parametrize("provider,merchant,count", [
    ("yatra", "yatra", 8), ("gyftr", "swiggy", 7), ("easemytrip", "easemytrip", 1),
])
def test_captured_public_response_contract(provider, merchant, count):
    adapter, html, context = captured(provider, merchant)
    offers = normalized(adapter, html, context)
    assert len(offers) == count
    assert all(o.verification_status == "VERIFIED" for o in offers)
    for offer in offers:
        assert ScrapedOffer.model_validate_json(offer.model_dump_json(by_alias=True)) == offer


def test_gyftr_prices_and_payment_conditions_are_preserved():
    adapter, html, context = captured("gyftr", "swiggy")
    offer = next(o for o in normalized(adapter, html, context) if o.voucher.face_value == 500)
    assert offer.voucher.selling_price == Decimal("487.50")
    assert offer.discount.value == Decimal("2.5")
    assert offer.eligible_instrument_types == ["UPI", "WALLET"]
    assert offer.valid_until is None and offer.minimum_transaction is None
    assert any("365 days" in term for term in offer.terms)


def test_gyftr_price_disagreement_keeps_both_observations():
    adapter, html, context = captured("gyftr", "swiggy")
    raw = next(r for r in adapter.parse(html, context) if r.face_value_text == "500")
    raw.selling_price_text = "450"
    offer, warnings = verify_offer(*normalize_offer(raw, context))
    assert offer.verification_status == "AMBIGUOUS" and offer.last_verified_at is None
    assert any("2.5" in warning and "450" in warning for warning in warnings)


def test_emt_minimum_and_formula_are_explicit():
    adapter, html, context = captured("easemytrip", "easemytrip")
    offer = normalized(adapter, html, context)[0]
    assert offer.minimum_transaction == offer.discount.maximum_discount == Decimal("1000")
    assert offer.discount.value == 20 and offer.promo_code == "GRAB20"
    assert offer.stacking_policy == "NOT_ALLOWED"
    without_minimum = html.replace("The minimum booking value to avail the offer is Rs.1000", "")
    assert normalized(adapter, without_minimum, context)[0].minimum_transaction is None


def test_yatra_does_not_flatten_passenger_or_category_restrictions():
    adapter, html, context = captured("yatra", "yatra")
    offers = normalized(adapter, html, context)
    assert len({o.external_key for o in offers}) == 8
    hotel = next(o for o in offers if "Domestic Hotels" in o.title)
    assert hotel.discount.value == 12 and hotel.discount.maximum_discount == 7500
    assert hotel.minimum_transaction == 3000 and hotel.promo_code == "YATRARBL"
    assert hotel.eligible_issuers == ["RBL"] and hotel.valid_until.month == 9
    assert any("one passenger for one-way" in o.title and o.discount.value == 650 for o in offers)


def test_expired_capture_is_not_authoritative():
    adapter, html, context = captured("yatra", "yatra")
    context = replace(context, scraped_at=context.scraped_at.replace(year=2027))
    assert all(o.verification_status == "AMBIGUOUS" for o in normalized(adapter, html, context))
