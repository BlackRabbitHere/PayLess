import json

from payment_scraper.cli import main
from payment_scraper.core.models import ScrapedOffer, ScrapeResponse
from payment_scraper.output.json_writer import write_json


def test_end_to_end_fixture_contract(service, tmp_path):
    result = service.scrape("gyftr", "swiggy money")
    assert result.status == "SUCCESS"
    assert result.metadata.fixture is True
    assert result.metadata.fetch_method == "FIXTURE"
    data = json.loads(result.model_dump_json(by_alias=True))
    assert data["offers"][0]["voucher"]["faceValue"] == "500.00"
    assert data["offers"][0]["voucher"]["sellingPrice"] == "487.50"
    assert data["startedAt"].endswith("Z")
    assert "scraped_at" not in data["offers"][0]
    assert ScrapeResponse.model_validate(data) == result
    assert ScrapedOffer.model_validate(data["offers"][0]) == result.offers[0]
    path = write_json(result, tmp_path / "offers.json")
    assert json.loads(path.read_text()) == data
    assert len(list((tmp_path / "raw").rglob("*.html"))) == 1


def test_structured_provider_errors(service):
    assert service.scrape("unknown", "swiggy").errors[0].code == "PROVIDER_NOT_SUPPORTED"
    assert service.scrape("GYFTR", "unknown").errors[0].code == "MERCHANT_NOT_SUPPORTED"


def test_cli_fixture(tmp_path, capsys, monkeypatch):
    from tests.conftest import FIXTURES

    monkeypatch.setenv("SAVE_RAW_HTML", "false")
    code = main(
        [
            "scrape",
            "--provider",
            "gyftr",
            "--merchant",
            "swiggy",
            "--fixture-dir",
            str(FIXTURES),
            "--output",
            str(tmp_path / "cli.json"),
            "--json",
        ]
    )
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["metadata"]["fixture"] is True
    assert data["offers"][0]["verificationStatus"] == "VERIFIED"
