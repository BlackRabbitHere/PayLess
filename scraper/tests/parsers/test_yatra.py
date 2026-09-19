from decimal import Decimal

from payment_scraper.core.models import ScrapedOffer


def test_yatra_same_contract_distinct_parser(service):
    result = service.scrape("YATRA", "YATRA")
    assert result.status == "SUCCESS"
    offer = result.offers[0]
    assert isinstance(offer, ScrapedOffer)
    assert offer.eligible_issuers == ["ICICI"]
    assert offer.eligible_instrument_types == ["CREDIT_CARD"]
    assert offer.transaction_mode == "EMI"
    assert offer.discount.value == Decimal("12")
    assert offer.discount.maximum_discount == Decimal("2000")
    assert offer.minimum_transaction == Decimal("5000")
    assert offer.stacking_policy == "NOT_ALLOWED"
    assert offer.promo_code == "FIXTURE12"
    assert offer.voucher is None
