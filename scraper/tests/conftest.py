import logging
from datetime import UTC, datetime
from pathlib import Path

import pytest

from payment_scraper.config.settings import Settings
from payment_scraper.core.enums import ProviderId
from payment_scraper.core.raw import ParseContext
from payment_scraper.services.scraping_service import build_service

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def restore_logging_handlers():
    logger = logging.getLogger("payment_scraper")
    handlers, level, propagate = logger.handlers[:], logger.level, logger.propagate
    yield
    logger.handlers, logger.level, logger.propagate = handlers, level, propagate


@pytest.fixture(autouse=True)
def no_network_in_offline_tests(request, monkeypatch):
    if request.node.get_closest_marker("live"):
        return

    def blocked(*args, **kwargs):
        raise AssertionError("Offline tests may not send real HTTP requests.")

    monkeypatch.setattr("requests.sessions.Session.request", blocked)


@pytest.fixture
def context():
    return ParseContext(
        ProviderId.GYFTR,
        "SWIGGY",
        "https://www.gyftr.com/swiggy-money",
        datetime(2026, 9, 18, 16, 30, tzinfo=UTC),
    )


@pytest.fixture
def fixture_html():
    return (FIXTURES / "gyftr_swiggy.html").read_text(encoding="utf-8")


@pytest.fixture
def service(tmp_path):
    instance = build_service(Settings(fixture_dir=FIXTURES, data_dir=tmp_path))
    yield instance
    instance.close()
