"""Fixture-only smoke through nginx -> Spring -> FastAPI (standard library only)."""
import datetime
import json
import sys
import urllib.request
import uuid

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:4173"

def call(path, data=None):
    request_id = str(uuid.uuid4())
    req = urllib.request.Request(base + path, data=json.dumps(data).encode() if data else None,
        headers={"Content-Type": "application/json", "X-Request-ID": request_id})
    with urllib.request.urlopen(req, timeout=75) as response:
        assert response.status == 200
        assert response.headers["X-Request-ID"] == request_id
        return json.load(response)

with urllib.request.urlopen(base + "/", timeout=10) as page:
    assert b'<div id="root">' in page.read()
status = call("/api/v1/system/status")
assert status["scraper"]["mode"] == "fixture", "Ordinary smoke requires fixtures; live tests are separate"
wallet = [{"issuer": "HDFC", "productName": "Millennia", "instrumentType": "CREDIT_CARD", "network": "VISA"}]
for _ in range(2):
    merchant = call("/api/optimize/query", {"query": "500 on swigy", "wallet": wallet})
    assert merchant["context"]["merchant"] == "SWIGGY"
    assert merchant["bestPayNowRoute"]["cost"]["payNow"] == 487.5
    assert merchant["sources"][0]["fixture"] is True
    assert not merchant["sources"][0]["errors"]
travel = call("/api/travel/optimize", {"origin": "Delhi", "destination": "Mumbai",
    "departureDate": str(datetime.date.today() + datetime.timedelta(days=10)), "passengers": 2, "wallet": wallet})
assert len(travel["fares"]) == 2
assert {s["provider"] for s in travel["optimization"]["sources"]} == {"YATRA", "EASEMYTRIP"}
assert all(s["fixture"] and not s["errors"] for s in travel["optimization"]["sources"])
assert travel["optimization"]["bestPayNowRoute"]["cost"]["payNow"] > 0
assert travel["routeFareIds"][travel["optimization"]["bestEffectiveCostRoute"]["id"]]
print("PASS: frontend, correlation, merchant repeat ingestion, travel, and all fixture providers")
