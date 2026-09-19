"""Export deterministic synthetic response examples and generated OpenAPI for Java clients."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from payment_scraper.api.app import create_app
from payment_scraper.config.settings import Settings
from payment_scraper.services.scraping_service import build_service

root = Path(__file__).resolve().parents[1]
destination = root / "tests" / "fixtures" / "contracts"
destination.mkdir(parents=True, exist_ok=True)
service = build_service(Settings(fixture_dir=root / "tests" / "fixtures", save_raw_html=False))
instant = datetime(2026, 9, 18, 16, 30, tzinfo=UTC)
try:
    for adapter in service.registry.all():
        for merchant in adapter.config.sources:
            result = service.scrape(adapter.config.provider, merchant)
            result.request_id = UUID("00000000-0000-4000-8000-000000000001")
            result.started_at = result.completed_at = instant
            for offer in result.offers:
                offer.scraped_at = instant
                if offer.last_verified_at:
                    offer.last_verified_at = instant
            (destination / f"{adapter.config.provider.lower()}_{merchant.lower()}.json").write_text(
                result.model_dump_json(indent=2, by_alias=True) + "\n", encoding="utf-8"
            )
    (destination / "openapi.json").write_text(
        json.dumps(create_app(service).openapi(), indent=2) + "\n", encoding="utf-8"
    )
finally:
    service.close()
