from decimal import Decimal

import pytest

from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.normalizer import normalize_offer
from payment_scraper.providers.gyftr.parser import parse


def test_semantic_fixture(fixture_html, context):
    raw = parse(fixture_html, context)
    assert raw[0].face_value_text == "₹500"
    offer, _ = normalize_offer(raw[0], context)
    assert offer.merchant == "SWIGGY"
    assert offer.voucher.face_value == Decimal("500.00")
    assert offer.voucher.selling_price == Decimal("487.50")
    assert str(offer.action_url) == context.source_url


def test_prices_are_extracted_not_hardcoded(fixture_html, context):
    changed = fixture_html.replace("₹500", "₹1,000").replace("₹487.50", "₹975")
    offer, _ = normalize_offer(parse(changed, context)[0], context)
    assert offer.voucher.face_value == Decimal("1000")
    assert offer.voucher.selling_price == Decimal("975")


def test_json_ld_decimal_and_missing_face_value(context):
    html = """<script type="application/ld+json">{"@type":"Product","name":"Swiggy Money",
    "offers":{"@type":"Offer","price":487.50,"priceCurrency":"INR"}}</script>"""
    raw = parse(html, context)[0]
    assert raw.selling_price_text == "487.50"
    assert raw.face_value_text is None
    assert raw.discount_text is None


def test_changed_dom_and_malformed_json(context):
    assert parse("<html>No offer data</html>", context) == []
    with pytest.raises(ScraperError):
        parse('<script type="application/ld+json">broken</script>', context)
