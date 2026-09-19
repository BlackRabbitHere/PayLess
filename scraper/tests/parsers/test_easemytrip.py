from decimal import Decimal


def test_easemytrip_payment_discount(service):
    result = service.scrape("EASEMYTRIP", "EASEMYTRIP")
    assert result.status == "SUCCESS"
    offer = result.offers[0]
    assert offer.transaction_mode == "UPI"
    assert offer.discount.value == Decimal("250")
    assert offer.discount.type == "FLAT"
    assert offer.discount.maximum_discount is None
    assert offer.minimum_transaction == Decimal("3000")
    assert offer.valid_until is None
    assert offer.eligible_issuers == []
