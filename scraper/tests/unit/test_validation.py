from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from payment_scraper.core.deduplicator import content_hash, deduplicate, identify
from payment_scraper.core.models import ScrapedOffer, Voucher
from payment_scraper.core.normalizer import normalize_offer
from payment_scraper.core.validator import verify_offer
from payment_scraper.providers.gyftr.parser import parse


def make_offer(html, context):
    raw = parse(html, context)[0]
    offer, warnings = normalize_offer(raw, context)
    offer, _ = verify_offer(offer, warnings)
    return identify(offer, raw.source_id)


def test_sanity_and_unknowns(fixture_html, context):
    offer = make_offer(fixture_html, context)
    assert offer.verification_status == "VERIFIED"
    assert offer.minimum_transaction is None
    assert offer.valid_until is None
    assert offer.discount.maximum_discount is None
    assert offer.voucher.face_value - offer.voucher.selling_price == Decimal("12.50")
    bad = make_offer(fixture_html.replace("2.5% OFF", "20% OFF"), context)
    assert bad.verification_status == "AMBIGUOUS"
    assert bad.last_verified_at is None


def test_conflicting_minima(fixture_html, context):
    raw = parse(fixture_html, context)[0]
    raw.minimum_transaction_texts = ["500", "1000"]
    offer, warnings = normalize_offer(raw, context)
    checked, _ = verify_offer(offer, warnings)
    assert checked.minimum_transaction is None
    assert checked.verification_status == "AMBIGUOUS"


def test_identity_stable_hash_changes(fixture_html, context):
    original = make_offer(fixture_html, context)
    later = make_offer(fixture_html, replace(context, scraped_at=context.scraped_at + timedelta(days=1)))
    changed = make_offer(fixture_html.replace("487.50", "480.00"), context)
    assert original.external_key == later.external_key == changed.external_key
    assert original.content_hash == later.content_hash
    assert original.content_hash != changed.content_hash
    assert content_hash(original) == original.content_hash
    deduped, warnings = deduplicate([original, original, changed])
    assert len(deduped) == 1
    assert deduped[0].verification_status == "AMBIGUOUS"
    assert warnings[0].code == "DUPLICATE_CONFLICT"
    assert deduplicate([changed, original])[0] == deduped
    equivalent = make_offer(fixture_html.replace("2.5% OFF", "2.50% OFF"), context)
    assert original.content_hash == equivalent.content_hash


@pytest.mark.parametrize("value", [-1, 1.2, True, "NaN", "Infinity", "1.001"])
def test_reject_bad_money(value):
    with pytest.raises(ValidationError):
        Voucher(face_value=value)


def test_contract_rejects_dates_urls_and_unknown_fields(fixture_html, context):
    data = make_offer(fixture_html, context).model_dump()
    for patch in (
        {"scraped_at": context.scraped_at.replace(tzinfo=None)},
        {"valid_from": context.scraped_at, "valid_until": context.scraped_at - timedelta(days=1)},
        {"source_url": "http://www.gyftr.com/x"},
        {"merchant": " "},
        {"unexpected": 2},
    ):
        with pytest.raises(ValidationError):
            ScrapedOffer.model_validate({**data, **patch})
