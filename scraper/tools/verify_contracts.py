"""Compare baseline exports and the recursively referenced canonical offer schema."""
import hashlib
import json
from pathlib import Path

from payment_scraper.core.models import ScrapedOffer


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def closure(document):
    schemas = document["components"]["schemas"]
    result = {}
    pending = ["ScrapedOffer"]
    def refs(value):
        if isinstance(value, dict):
            if "$ref" in value:
                yield value["$ref"].rsplit("/", 1)[-1]
            for item in value.values():
                yield from refs(item)
        elif isinstance(value, list):
            for item in value:
                yield from refs(item)
    while pending:
        name = pending.pop()
        if name not in result:
            result[name] = schemas[name]
            pending.extend(refs(schemas[name]))
    return result


root = Path(__file__).resolve().parents[1]
baseline = root / "data/verification/baseline"
exports = root / "tests/fixtures/contracts"
old_api = json.loads((baseline / "openapi.json").read_text())
new_api = json.loads((exports / "openapi.json").read_text())
before = closure(old_api)
after = closure(new_api)
assert before == after, "Canonical ScrapedOffer schema changed."
assert all(new_api["paths"].get(path) == value for path, value in old_api["paths"].items())
assert set(new_api["paths"]) - set(old_api["paths"]) == {"/api/v1/offers"}
old_schemas, new_schemas = old_api["components"]["schemas"], new_api["components"]["schemas"]
assert set(old_schemas) == set(new_schemas)
assert {name for name in old_schemas if old_schemas[name] != new_schemas[name]} == {
    "ProviderInfo", "ErrorCode",
}
assert old_schemas["ProviderInfo"]["required"] == new_schemas["ProviderInfo"]["required"]
assert all(new_schemas["ProviderInfo"]["properties"][key] == value
           for key, value in old_schemas["ProviderInfo"]["properties"].items())
assert set(old_schemas["ErrorCode"]["enum"]) <= set(new_schemas["ErrorCode"]["enum"])
accepted = (root / "contracts/openapi.sha256").read_text().strip()
assert digest(exports / "openapi.json") == accepted, "OpenAPI differs from the accepted frozen baseline."
report = {}
for old in sorted(baseline.glob("*.json")):
    current = exports / old.name
    if current.exists():
        report[old.name] = {"before": digest(old), "after": digest(current),
                            "unchanged": old.read_bytes() == current.read_bytes()}
        if old.name != "openapi.json":
            assert report[old.name]["unchanged"], old.name
canonical = json.dumps(before, sort_keys=True, separators=(",", ":")).encode()
report["canonicalOffer"] = {"unchanged": True, "sha256": hashlib.sha256(canonical).hexdigest()}
report["openapiReview"] = {
    "acceptedBaseline": accepted, "matchesAcceptedBaseline": True,
    "changes": [
        "Adds GET /api/v1/offers with the existing ApiErrorResponse for validation/internal errors.",
        "Adds optional ProviderInfo health fields; existing required fields are unchanged.",
        "Adds precise ErrorCode values; all legacy values remain accepted.",
    ],
    "compatibility": "Existing endpoints and canonical offers unchanged. Error DTO uses string codes; "
                     "strict old enum clients must regenerate and clients must tolerate optional fields.",
}
folder = root / "contracts"
folder.mkdir(exist_ok=True)
(folder / "scraped_offer.schema.json").write_text(
    json.dumps(ScrapedOffer.model_json_schema(by_alias=True, mode="serialization"), indent=2) + "\n",
    encoding="utf-8",
)
for example in folder.glob("live_*_example.json"):
    offer = ScrapedOffer.model_validate_json(example.read_text(encoding="utf-8"))
    assert offer.verification_status == "VERIFIED"
    assert offer.model_dump(mode="json", by_alias=True) == json.loads(example.read_text(encoding="utf-8"))
(root / "data/verification/contract-comparison.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8",
)
print(json.dumps(report, indent=2))
