import pytest

from payment_scraper.core.deduplicator import content_hash
from payment_scraper.core.models import ScrapedOffer, ScrapeResponse
from tests.conftest import FIXTURES


@pytest.mark.parametrize(
    "provider,merchant", [("GYFTR", "SWIGGY"), ("YATRA", "YATRA"), ("EASEMYTRIP", "EASEMYTRIP")]
)
def test_same_canonical_contract_for_every_provider(service, provider, merchant):
    result = service.scrape(provider, merchant)
    assert result.status == "SUCCESS"
    assert result.metadata.fixture
    assert len(result.offers) == 1
    assert isinstance(result.offers[0], ScrapedOffer)
    assert ScrapeResponse.model_validate_json(result.model_dump_json(by_alias=True)) == result
    assert result.offers[0].provider == provider


@pytest.mark.parametrize("name", ["gyftr_swiggy", "yatra_yatra", "easemytrip_easemytrip"])
def test_java_response_fixtures(name):
    result = ScrapeResponse.model_validate_json(
        (FIXTURES / "contracts" / f"{name}.json").read_text(encoding="utf-8")
    )
    assert result.metadata.fixture
    assert result.status == "SUCCESS"
    for offer in result.offers:
        assert offer.content_hash == content_hash(offer)
