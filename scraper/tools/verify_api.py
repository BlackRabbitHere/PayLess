"""Verify real HTTP endpoints using a temporary host server or an existing Docker origin."""
import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests

from payment_scraper.core.models import ScrapedOffer, ScrapeResponse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", help="Existing HTTP server; otherwise start/close local Uvicorn.")
    parser.add_argument("--label", default="host")
    args = parser.parse_args()
    folder = Path("data/verification")
    folder.mkdir(parents=True, exist_ok=True)
    process = None
    session = requests.Session()
    session.trust_env = False
    log = (folder / f"{args.label}_api.log").open("wb")
    try:
        origin = args.origin
        if not origin:
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            origin = f"http://127.0.0.1:{port}"
            process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "payment_scraper.api.app:app",
                 "--host", "127.0.0.1", "--port", str(port), "--workers", "1"],
                env={**os.environ, "FIXTURE_DIR": ""}, stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        deadline = time.monotonic() + 15
        while True:
            try:
                health = session.get(origin + "/health", timeout=2)
                health.raise_for_status()
                assert health.json()["mode"] == "live"
                break
            except requests.ConnectionError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.2)
        assert "swagger-ui" in session.get(origin + "/docs", timeout=5).text
        openapi = session.get(origin + "/openapi.json", timeout=5).json()
        assert "/api/v1/scrape" in openapi["paths"] and "/api/v1/offers" in openapi["paths"]
        assert openapi == json.loads(Path("tests/fixtures/contracts/openapi.json").read_text())
        schema = session.get(origin + "/api/v1/schema/offers", timeout=5).json()["jsonSchema"]
        assert schema == ScrapedOffer.model_json_schema(by_alias=True, mode="serialization")
        report = {"origin": origin, "health": health.json(), "swagger": 200,
                  "openapi": 200, "canonicalSchemaMatches": True, "providers": {}, "cache": {}}
        for provider, merchant in (("YATRA", "YATRA"), ("GYFTR", "SWIGGY"), ("EASEMYTRIP", "EASEMYTRIP")):
            response = session.post(origin + "/api/v1/scrape", json={
                "provider": provider, "merchant": merchant, "forceRefresh": False,
            }, timeout=180)
            result = ScrapeResponse.model_validate(response.json())
            assert response.status_code == 200 and result.status == "SUCCESS" and result.offers
            assert not result.metadata.fixture and not result.metadata.cache_hit
            repeat = session.post(origin + "/api/v1/scrape", json={
                "provider": provider, "merchant": merchant, "forceRefresh": False,
            }, timeout=180)
            cached = ScrapeResponse.model_validate(repeat.json())
            assert cached.metadata.cache_hit and cached.offers == result.offers
            refreshed = session.post(origin + "/api/v1/scrape", json={
                "provider": provider, "merchant": merchant, "forceRefresh": True,
            }, timeout=180)
            fresh = ScrapeResponse.model_validate(refreshed.json())
            assert refreshed.status_code == 200 and fresh.status == "SUCCESS"
            assert not fresh.metadata.fixture and not fresh.metadata.cache_hit
            assert [o.external_key for o in fresh.offers] == [o.external_key for o in result.offers]
            report["cache"][provider] = {
                "firstRequestHit": result.metadata.cache_hit, "secondRequestHit": cached.metadata.cache_hit,
                "forceRefreshHit": fresh.metadata.cache_hit,
                "cachedTimestampsPreserved": cached.offers == result.offers,
            }
            result, response = fresh, refreshed
            for offer in result.offers:
                assert offer.provider == provider and offer.merchant == merchant
                assert offer.verification_status == "VERIFIED"
                assert offer.last_verified_at == offer.scraped_at >= result.started_at
                assert urlsplit(str(offer.source_url)).hostname in {provider.lower() + ".com",
                                                                  "www." + provider.lower() + ".com"}
            example = Path("contracts") / f"live_{provider.lower()}_example.json"
            example.write_text(result.offers[0].model_dump_json(by_alias=True, indent=2), encoding="utf-8")
            (folder / f"{args.label}_api_{provider.lower()}.json").write_text(
                result.model_dump_json(by_alias=True, indent=2), encoding="utf-8",
            )
            report["providers"][provider] = {
                "httpStatus": response.status_code, "status": result.status,
                "offers": len(result.offers), "requestId": str(result.request_id),
                "failures": [e.code for e in result.errors],
            }
            print(f"{args.label} {provider}: HTTP {response.status_code}, {result.status}, "
                  f"{len(result.offers)} offers", flush=True)
        # Reuses the successful HTTP cache, avoiding a second round of public requests.
        aggregate = session.get(origin + "/api/v1/offers", timeout=180)
        assert aggregate.status_code == 200 and len(aggregate.json()) == 3
        report["aggregate"] = [{"provider": r["provider"], "offers": len(r["offers"]),
                                "cacheHit": r["metadata"]["cacheHit"]} for r in aggregate.json()]
        report["providerHealth"] = session.get(origin + "/api/v1/providers", timeout=5).json()
        (folder / f"{args.label}_api_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8",
        )
        assert all(p["offers"] for p in report["providers"].values()), report
        assert all(p["liveVerified"] for p in report["providerHealth"]["providers"]), report
    finally:
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        session.close()
        log.close()


if __name__ == "__main__":
    main()
