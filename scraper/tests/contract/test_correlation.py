import json
import logging
from uuid import UUID

from fastapi.testclient import TestClient

from payment_scraper.api.app import create_app
from payment_scraper.core.logging_config import JsonFormatter, request_context, scrape_context


def test_correlation_round_trip_and_invalid_header(service):
    with TestClient(create_app(service)) as client:
        response = client.post("/api/v1/scrape", headers={"X-Request-ID": "browser-123"},
                               json={"provider": "GYFTR", "merchant": "SWIGGY"})
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == "browser-123"
        UUID(response.json()["requestId"])
        assert request_context.get() is None
        response = client.get("/health", headers={"X-Request-ID": "invalid id"})
        UUID(response.headers["X-Request-ID"])
        response = client.post("/api/v1/scrape", headers={"X-Request-ID": "error-123"}, json={})
        assert response.status_code == 422
        assert response.headers["X-Request-ID"] == "error-123"


def test_logs_link_browser_request_and_scraper_run_without_overwriting_contract_id():
    token = request_context.set("browser-123")
    scrape_token = scrape_context.set({"requestId": "scrape-456", "merchant": "SWIGGY"})
    try:
        record = logging.LogRecord("payment_scraper", logging.INFO, "", 0, "scrape_completed", (), None)
        result = json.loads(JsonFormatter().format(record))
        assert result["requestId"] == "browser-123"
        assert result["scraperRequestId"] == "scrape-456"
    finally:
        request_context.reset(token)
        scrape_context.reset(scrape_token)
