from urllib.parse import urlsplit

import pytest

from payment_scraper.config.settings import Settings
from payment_scraper.core.models import ScrapeResponse, utc_now
from payment_scraper.services.scraping_service import build_service


def assert_live_provider(provider, merchant):
    settings = Settings.from_env()
    if not getattr(settings, f"provider_{provider.lower()}_enabled"):
        pytest.skip(f"{provider} disabled by application configuration.")
    if settings.fixture_dir:
        pytest.fail("Live verification requires FIXTURE_DIR to be empty.")
    service = build_service(settings)
    started = utc_now()
    try:
        result = service.scrape(provider, merchant, force_refresh=True)
        domains = service.registry.get(provider).config.allowed_domains
    finally:
        service.close()
    assert result.status in {"SUCCESS", "PARTIAL"}, result.model_dump_json(by_alias=True)
    assert not result.metadata.fixture
    assert result.metadata.fetch_method in {"HTTP", "BROWSER"}
    assert result.metadata.offers_found >= 1 and result.offers
    assert not result.errors
    assert not any(warning.code == "FIXTURE_DATA" for warning in result.warnings)
    assert ScrapeResponse.model_validate_json(result.model_dump_json(by_alias=True)) == result
    for offer in result.offers:
        assert offer.title and offer.merchant == merchant and offer.provider == provider
        assert urlsplit(str(offer.source_url)).hostname in domains
        assert offer.source_url.scheme == "https"
        assert offer.scraped_at >= started
        assert offer.verification_status in {"VERIFIED", "AMBIGUOUS"}
        if offer.verification_status == "VERIFIED":
            assert offer.last_verified_at == offer.scraped_at
        for amount in (offer.discount.value, offer.discount.maximum_discount, offer.minimum_transaction):
            assert amount is None or amount >= 0
