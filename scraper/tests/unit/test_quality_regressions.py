from payment_scraper.core.deduplicator import deduplicate, identify
from payment_scraper.core.enums import VerificationStatus
from payment_scraper.core.normalizer import normalize_offer
from payment_scraper.core.validator import verify_offer
from payment_scraper.providers.gyftr.parser import parse


def test_duplicate_conflict_never_promotes_incomplete_offer(fixture_html, context):
    raw = parse(fixture_html, context)[0]
    raw.selling_price_text = None
    first, warnings = normalize_offer(raw, context)
    first, _ = verify_offer(first, warnings)
    first = identify(first, raw.source_id)
    raw.discount_text = "20%"
    second, warnings = normalize_offer(raw, context)
    second, _ = verify_offer(second, warnings)
    second = identify(second, raw.source_id)
    result, _ = deduplicate([first, second])
    assert result[0].verification_status == "INCOMPLETE"


def test_same_content_does_not_erase_conflict_status(fixture_html, context):
    raw = parse(fixture_html, context)[0]
    offer, warnings = normalize_offer(raw, context)
    offer, _ = verify_offer(offer, warnings)
    offer = identify(offer, raw.source_id)
    ambiguous = offer.model_copy(
        update={"verification_status": VerificationStatus.AMBIGUOUS, "last_verified_at": None}
    )
    for observations in ([offer, ambiguous], [ambiguous, offer]):
        unique, _ = deduplicate(observations)
        assert unique[0].verification_status == "AMBIGUOUS"
        assert unique[0].last_verified_at is None
