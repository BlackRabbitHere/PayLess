# Final verification — 2026-09-19

**Frozen and ready for Spring Boot integration.** All three providers return genuine public
offers on Windows and Docker. No fixture was substituted for a live response. The canonical
ScrapedOffer is unchanged. The intentional OpenAPI update has an explicitly accepted baseline.

| Provider | Final live status | Windows offers | Docker offers | API outcome |
| --- | --- | ---: | ---: | --- |
| YATRA | LIVE VERIFIED | 8 | 8 | HTTP 200 / SUCCESS |
| GYFTR | LIVE VERIFIED | 7 | 7 | HTTP 200 / SUCCESS |
| EASEMYTRIP | LIVE VERIFIED | 1 | 1 | HTTP 200 / SUCCESS |

Final evidence is in `data/verification/host_api_report.json`,
`data/verification/docker_api_report.json`, `docker-status.json` and
`contract-comparison.json`. These record actual responses, assertions and request IDs.

## Offline tests

- Initial baseline: **102 passed**, 5 opt-in tests deselected.
- Final: **131 passed**, 5 opt-in tests deselected; no failures.
- All original test cases remain; tests asserting the previous robots/terms gate and coarse
  failure codes were updated to the explicitly requested behavior.
- New coverage includes captured live DOM, canonical round trips, voucher discrepancies,
  payment/category restrictions, absent minimums, transport diagnostics, bounded fallback,
  URL safety, partial aggregation, immutable source identity and OpenAPI validation errors.
- **Ruff passed** and **compileall passed**.
- Two pre-existing Starlette/httpx and AnyIO deprecation warnings remain.
- Live/browser tests are opt-in. Their separate run passed **3 live provider tests and
  2 real Chromium rendering/cleanup tests**. This does not make default CI depend on websites.

## HTTP fetch verification

All current curated URLs returned HTTP 200 and actual public offer HTML. Requests uses a
persistent session, TLS verification, explicit connect/read bounds, normal headers, default
zero retries and configurable host pacing. Robots observations are informational; provider
activation remains separate. Fixture mode was false for every final live response.

## Playwright live verification

Ordinary Chromium navigated to GyFTR's public Swiggy page and produced seven VERIFIED offers,
with rendered DOM snapshots, on Windows and Linux/Docker. Evidence:
`data/verification/browser_gyftr.json` and `docker_browser_gyftr.json`.
The browser uses native networking and closes page/context/browser/Playwright.

Earlier Yatra browser attempts reported ERR_HTTP2_PROTOCOL_ERROR. An EaseMyTrip browser
attempt returned HTTP 502. Their successful final acquisition uses HTTP; successful browser
fallback for those two providers is not claimed. No challenge solving, authentication,
fingerprint changes or blocking evasion was attempted.

## Yatra

**LIVE VERIFIED — 8 offers.**

Source: [public RBL offer](https://www.yatra.com/offer/details/rbl-credit-card-offers).
The parser preserves the separate passenger/trip/category conditions, coupon YATRARBL,
RBL credit-card requirement, minimum booking amounts and September 2026 validity.
The expired ICICI page is no longer the live source; its original synthetic fixture URL
remains unchanged for contract compatibility.

## GyFTR

**LIVE VERIFIED — 7 offers.**

Source: [public Swiggy vouchers](https://www.gyftr.com/swiggy-gv).
The obsolete /swiggy-money path returned a shell. The current page supplies displayed face
values, selling prices and embedded product/payment-method data. INR 500 versus INR 487.50
is an observed example: saving INR 12.50, percentage 2.5%. Payment conditions remain in the
canonical instruments/terms. Amounts use Decimal and discrepancies become AMBIGUOUS.

## EaseMyTrip

**LIVE VERIFIED — 1 offer.**

Source: [public hotel offer](https://www.easemytrip.com/offers/flash-sale-on-hotel.html).
The page explicitly states coupon GRAB20, 20% capped at INR 1,000, a minimum of INR 1,000,
selected properties and no clubbing. Validity is normalized through 30 September 2026.
The earlier bank-deals listing contained no active usable offers; it is not presented as
a successful source.

## Raw snapshots

The final forced-refresh API responses have these immutable raw captures. Docker paths
are in the persistent scraper-data volume; Windows paths are relative to the project root.
Each has a JSON sidecar with actual source/request/final URL, request ID, status, byte count,
encoding, timing, redirect chain, SHA-256 and HTTP fetchMethod.

| Provider | Windows snapshot | Final Docker snapshot |
| --- | --- | --- |
| YATRA | `data/raw/yatra/yatra/20260919T025033411244Z_86fa8b25d79b9cf9.html` | `/app/data/raw/yatra/yatra/20260919T025510514971Z_c6b8fc42828c35af.html` |
| GYFTR | `data/raw/gyftr/swiggy/20260919T025039740676Z_af78ebadafa1c20c.html` | `/app/data/raw/gyftr/swiggy/20260919T025516767454Z_af78ebadafa1c20c.html` |
| EASEMYTRIP | `data/raw/easemytrip/easemytrip/20260919T025046044309Z_eb9b93cc27431004.html` | `/app/data/raw/easemytrip/easemytrip/20260919T025523052511Z_eb9b93cc27431004.html` |

The separately verified Docker browser capture is:
`/app/data/raw/gyftr/swiggy/20260919T023052404410Z_797477bddb696304.html`,
with fetchMethod=PLAYWRIGHT. Snapshot retention still applies.

Sanitized permanent regression fixtures are:
`tests/fixtures/live/yatra_yatra.html`,
`tests/fixtures/live/gyftr_swiggy.html` and
`tests/fixtures/live/easemytrip_easemytrip.html`.
Their JSON sidecars record capturedFromLive=true, captureDate, source URL, original hash,
sanitized hash and request ID. They were generated from actual successful response snapshots.
Running these fixtures is an offline regression, not a fresh live verification.

## Normalized output

Final examples were refreshed from the final Docker responses, validated with the exact
canonical Pydantic model, and checked for provider/merchant, source hostname,
verificationStatus=VERIFIED, and lastVerifiedAt=scrapedAt after the request began.

| Provider / merchant | Genuine saved example | lastVerifiedAt = scrapedAt | Status |
| --- | --- | --- | --- |
| YATRA / YATRA | [live_yatra_example.json](../contracts/live_yatra_example.json) | 2026-09-19T02:55:10.514971Z | VERIFIED |
| GYFTR / SWIGGY | [live_gyftr_example.json](../contracts/live_gyftr_example.json) | 2026-09-19T02:55:16.767454Z | VERIFIED |
| EASEMYTRIP / EASEMYTRIP | [live_easemytrip_example.json](../contracts/live_easemytrip_example.json) | 2026-09-19T02:55:23.052511Z | VERIFIED |

Unknown fields remain null/UNKNOWN. No optimizer, user eligibility ranking, effective cost,
or payment route was computed. DEMO/FAILED remain diagnostic classifications outside the
unchanged canonical verification enum; production ingestion checks fixture=false and VERIFIED.

## CLI

All three requested CLI commands exited **0** with SUCCESS and counts **8 / 7 / 1**.
Complete UTF-8 envelopes and request logs:
`data/verification/live_yatra_cli.json`,
`live_gyftr_cli.json`, `live_easemytrip_cli.json` and their matching .log files.
CLI fixture mode remains explicit and never serves as live fallback.

## FastAPI

Windows Uvicorn and Docker both passed /health (live), /docs (Swagger), /openapi.json and
/api/v1/schema/offers. The served OpenAPI matched the accepted generated artifact, and the
served offer schema matched the canonical serialization schema exactly.

POST /api/v1/scrape returned HTTP 200, SUCCESS, no errors and 8/7/1 real offers. Full envelopes
are `data/verification/host_api_<provider>.json` and `docker_api_<provider>.json`.

| Provider | Final Windows request ID | Final Docker request ID |
| --- | --- | --- |
| YATRA | `40f6f3c3-a1a2-4fc0-987a-e740064b2af6` | `22eacd24-060d-4bac-a497-3883063244f0` |
| GYFTR | `73856564-ada5-4ff5-976f-14c40d0d77eb` | `9c859ca6-1f04-424e-8802-e483051a0e3c` |
| EASEMYTRIP | `d31ab72a-bb7a-4dc8-956a-9cb60836d8fe` | `51618a85-f792-43bc-b518-3e80f113c691` |

GET /api/v1/offers returned three independent envelopes with cacheHit=true. Offline failure
injection confirms that one provider's failure retains other providers' results. No real
provider outage was induced merely to test this.

Final Docker /api/v1/providers output:

```json
{
  "schemaVersion": 1,
  "providers": [
    {
      "provider": "GYFTR",
      "merchants": [
        "SWIGGY"
      ],
      "browserFallback": true,
      "liveReady": true,
      "termsReviewed": false,
      "enabled": true,
      "httpReady": true,
      "browserReady": true,
      "parserReady": true,
      "sourceReachable": true,
      "liveVerified": true,
      "lastSuccessfulScrape": "2026-09-19T02:55:23.233007+00:00",
      "lastFailure": null,
      "lastCheckedAt": "2026-09-19T02:55:23.233007+00:00"
    },
    {
      "provider": "YATRA",
      "merchants": [
        "YATRA"
      ],
      "browserFallback": true,
      "liveReady": true,
      "termsReviewed": false,
      "enabled": true,
      "httpReady": true,
      "browserReady": true,
      "parserReady": true,
      "sourceReachable": true,
      "liveVerified": true,
      "lastSuccessfulScrape": "2026-09-19T02:55:23.298170+00:00",
      "lastFailure": null,
      "lastCheckedAt": "2026-09-19T02:55:23.298170+00:00"
    },
    {
      "provider": "EASEMYTRIP",
      "merchants": [
        "EASEMYTRIP"
      ],
      "browserFallback": true,
      "liveReady": true,
      "termsReviewed": false,
      "enabled": true,
      "httpReady": true,
      "browserReady": true,
      "parserReady": true,
      "sourceReachable": true,
      "liveVerified": true,
      "lastSuccessfulScrape": "2026-09-19T02:55:23.456069+00:00",
      "lastFailure": null,
      "lastCheckedAt": "2026-09-19T02:55:23.456069+00:00"
    }
  ]
}
```

browserReady reports configured capability; the separate browser evidence establishes actual
Chromium operation. liveVerified is an observed status, with lastCheckedAt, not an uptime promise.

## Cache

Verified independently for **all three providers on Windows and Docker**, starting with a cold
worker:

| Request | cacheHit | Observed behavior |
| --- | --- | --- |
| First normal POST | false | Real public response |
| Identical normal POST | true | Identical offers and original source timestamps |
| POST with forceRefresh=true | false | New fetch, stable external keys, current timestamps |

The reports contain these assertions under cache. The cache is process-local; separate CLI
processes do not share it.

## Docker

The final image built successfully and container `scraper-scraper-1` is running and **healthy**.
Build output: `data/verification/docker-build.log`.
Status: `data/verification/docker-status.json`.
The final image includes the corrected OpenAPI error declaration.

All three live providers, canonical schema, Swagger, API health, provider health, source
snapshot writes and miss/hit/force-refresh checks passed in the final container. Native
Chromium public navigation and parsing also passed in Docker as recorded above.
The running service remains at http://127.0.0.1:8000.

## Spring contract compatibility and OpenAPI review

The complete recursively referenced ScrapedOffer schema is **unchanged**, SHA-256:
`5528f01912c36972c2153ee26cc53f04e8bcfb156aef07b668bdba5365d037dc`.

All three original generated response examples are byte-for-byte unchanged:

| Contract file | SHA-256 before = after |
| --- | --- |
| yatra_yatra.json | fa7cf154038ba0bcce7750067eaddbbea62cafb9d04862014f304297c0f4cea1 |
| gyftr_swiggy.json | 1abce20060f7e7c0b59b8a96528bc12301b9b2ca23f40567609555fb4dd1d65e |
| easemytrip_easemytrip.json | ffce2e7c8e24ba348af5b1536815921c9303aa9096902b6211618167967270e7 |

OpenAPI was inspected structurally. Intentional additions:
1. GET /api/v1/offers with independent provider envelopes.
2. Optional ProviderInfo health fields. Existing properties and required fields are unchanged.
3. Detailed ErrorCode strings. Every legacy enum value remains present.

No existing path definition or canonical offer component changed. The one accidental change
was FastAPI's default validation error schema on the new aggregate path. It was corrected to
the existing ApiErrorResponse (422 and internal 500) and regression-tested. Spurious
HTTPValidationError/ValidationError components are no longer added.

Original OpenAPI hash:
`66a29b21abca35d1634518931459dc3861e80e3a598d5ca0d82544d8e9606495`.

**Accepted frozen OpenAPI hash**:
`a3b97003fc82f98f3ef5c249fa832e34ca4e7164ebc80a676f48157cd522114a`.

The new baseline is pinned in `contracts/openapi.sha256`; tools/verify_contracts.py asserts it.
The historical before/after difference is intentional, explained and accepted. No unresolved
hash mismatch remains. Compatibility assumes the documented string error DTO and tolerance
for additive optional response fields; strict old generated enum clients must regenerate.

Spring Boot should use **POST http://127.0.0.1:8000/api/v1/scrape**. Exact requests, response
structure, timeouts and partial-failure handling are documented in
[spring-boot-integration.md](spring-boot-integration.md).

## Final verification commands

Executed from `F:\SpringBoot\Devathon Hackathon\Scrapper\scraper` (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m pytest --tb=short -p no:cacheprovider
.\.venv\Scripts\ruff.exe check --no-cache src tests tools
.\.venv\Scripts\python.exe -m compileall -q src tools
.\.venv\Scripts\python.exe tools/export_contracts.py
.\.venv\Scripts\python.exe tools/verify_contracts.py

$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) 'data/browsers'
.\.venv\Scripts\python.exe -m pytest -m 'live or browser' -vv --tb=short -p no:cacheprovider
.\.venv\Scripts\python.exe tools/verify_live.py
.\.venv\Scripts\python.exe tools/verify_live.py --browser

.\.venv\Scripts\python.exe -m payment_scraper.cli scrape --provider yatra --merchant yatra --force-refresh --json
.\.venv\Scripts\python.exe -m payment_scraper.cli scrape --provider gyftr --merchant swiggy --force-refresh --json
.\.venv\Scripts\python.exe -m payment_scraper.cli scrape --provider easemytrip --merchant easemytrip --force-refresh --json

.\.venv\Scripts\python.exe tools/verify_api.py
docker compose build > data/verification/docker-build.log 2>&1
docker compose up -d --wait
docker compose ps --format json > data/verification/docker-status.json
.\.venv\Scripts\python.exe tools/verify_api.py --origin http://127.0.0.1:8000 --label docker
Get-Content -Raw tools/verify_live.py | docker compose exec -T scraper python - --browser
docker compose cp scraper:/app/data/diagnostics data/verification/docker-diagnostics
docker compose cp scraper:/app/data/verification/browser_gyftr.json data/verification/docker_browser_gyftr.json
```

verify_api.py checks /health, /docs, /openapi.json, /api/v1/schema/offers,
/api/v1/providers, each live scrape, aggregate results and cache behavior. It requires a cold
worker for its first-miss assertion and closes its temporary Windows server after verification.
The final contract check was rerun after exporting the newest live examples.

## Remaining limitations

- Public page availability and markup can change; the verified scope is the three curated URLs,
  not every offer or merchant from each provider.
- Yatra and EaseMyTrip's successful paths are HTTP. Their earlier browser protocol/server errors
  remain documented; native browser success is independently established for GyFTR.
- Cache and pacing are process-local; use one worker/replica. Health is the latest observation.
- Unknown expiry, eligibility, availability and category/payment restrictions need explicit
  backend policies; VERIFIED is source consistency, not universal user eligibility.
- Old clients with closed error enums or forbidden extra response properties must regenerate
  against the accepted OpenAPI. Canonical offer DTOs do not need a schema change.
- Two existing dependency deprecation warnings remain. No provider-specific HTTP blocker remains
  for the final curated sources.

No further features are planned in this task. The scraper is frozen for backend integration.
