from fastapi.testclient import TestClient

from payment_scraper.api.app import create_app
from payment_scraper.core.models import ScrapeResponse


def test_api_and_openapi(service):
    with TestClient(create_app(service)) as client:
        assert client.get("/health").json() == {"status": "ok", "schemaVersion": 1, "mode": "fixture"}
        providers = client.get("/api/v1/providers").json()["providers"]
        assert providers[0]["provider"] == "GYFTR"
        result = client.post("/api/v1/scrape", json={"provider": "GYFTR", "merchant": "SWIGGY"})
        assert result.status_code == 200
        parsed = ScrapeResponse.model_validate(result.json())
        assert parsed.offers[0].verification_status == "VERIFIED"
        assert parsed.metadata.fixture
        schema = client.get("/openapi.json")
        assert schema.status_code == 200
        assert "/api/v1/scrape" in schema.json()["paths"]
        models = schema.json()["components"]["schemas"]
        assert "ScrapedOffer" in models
        voucher_schema = models["Voucher"]["properties"]["faceValue"]
        assert any(branch.get("type") == "string" for branch in voucher_schema["anyOf"])
        offer_schema = client.get("/api/v1/schema/offers").json()["jsonSchema"]
        assert "externalKey" in offer_schema["properties"]
        assert client.get("/docs").status_code == 200


def test_api_rejects_arbitrary_urls_and_bad_input(service):
    with TestClient(create_app(service)) as client:
        unsupported = client.post("/api/v1/scrape", json={"provider": "BAD", "merchant": "SWIGGY"})
        assert unsupported.status_code == 400
        assert unsupported.json()["errors"][0]["code"] == "PROVIDER_NOT_SUPPORTED"
        for body in (
            {},
            {"provider": "GYFTR", "merchant": "SWIGGY", "url": "http://127.0.0.1"},
            {"provider": "GYFTR", "merchant": "../secrets"},
        ):
            result = client.post("/api/v1/scrape", json=body)
            assert result.status_code == 422
            assert "127.0.0.1" not in result.text
            assert "traceback" not in result.text.lower()
