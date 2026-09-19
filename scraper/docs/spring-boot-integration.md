# Spring Boot integration — frozen scraper v1

The scraper is frozen for backend integration as of 2026-09-19. Windows and Docker return
genuine public offers for Yatra, GyFTR and EaseMyTrip. No Java application was added.
Spring Boot owns eligibility, ranking, effective cost, payment routes and user-facing actions.

## Endpoint to call

Use **POST /api/v1/scrape** for one provider/merchant. With the current Docker port mapping,
the exact local URL is **http://127.0.0.1:8000/api/v1/scrape**. A backend in another container
must use a reachable scraper service address; its own localhost is not the scraper.

Header: `Content-Type: application/json`.

```json
{
  "provider": "GYFTR",
  "merchant": "SWIGGY",
  "forceRefresh": false
}
```

Supported pairs are YATRA/YATRA, GYFTR/SWIGGY and EASEMYTRIP/EASEMYTRIP. Identifiers are
case-insensitive. The request rejects unknown fields and does not accept arbitrary source URLs.
Use forceRefresh=true only when a fresh provider response is required.

## Exact response format

POST returns one `ScrapeResponse` object:

| Property | JSON type and meaning |
| --- | --- |
| schemaVersion | Integer, currently 1 |
| requestId | UUID string for diagnostics |
| status | SUCCESS, PARTIAL or FAILED |
| provider, merchant | Normalized identifier strings |
| startedAt, completedAt | UTC ISO timestamp strings |
| offers | Array of canonical ScrapedOffer objects |
| warnings | Array of {code, message, externalKey}; externalKey may be null |
| errors | Array of {code, message, provider, retryable}; code is a string |
| metadata | {cacheHit, fetchMethod, offersFound, offersExcluded, fixture} |

fetchMethod is HTTP, BROWSER, FIXTURE or null. Source snapshot sidecars spell the BROWSER
implementation PLAYWRIGHT; the existing response enum is unchanged. The canonical offer's
maximum discount remains **discount.maximumDiscount**, not a new top-level field.

The exact serialization schema is [scraped_offer.schema.json](../contracts/scraped_offer.schema.json)
and is served by **GET /api/v1/schema/offers**, under jsonSchema. The full API document is
**GET /openapi.json**. Genuine complete offer examples are:

- [Yatra](../contracts/live_yatra_example.json)
- [GyFTR](../contracts/live_gyftr_example.json)
- [EaseMyTrip](../contracts/live_easemytrip_example.json)

Full live response envelopes are saved in `data/verification/docker_api_<provider>.json`.
The examples and envelopes validate with the unchanged Pydantic canonical model, retain
their actual sourceUrl and scrapedAt/lastVerifiedAt, and were not created from fixtures.

Money is serialized as decimal strings such as "487.50"; use Java BigDecimal, never double.
Percentage values are decimal strings in percentage points. Use Instant for UTC timestamps.
Preserve nulls and UNKNOWN; absent issuer restrictions are not proof of universal eligibility.
sourceUrl identifies the evidence page; actionUrl is separately domain-validated.

## Timeout and error behavior

The endpoint is synchronous. Configure a backend connection timeout of **5 seconds** and a
read timeout of **180 seconds** for a single-provider background request. This is a recommended
client bound, not an API latency guarantee. HTTP acquisition defaults to 5 seconds connect,
25 seconds read and zero retries. Ordinary browser fallback has a 30-second navigation bound,
8-second selector bound and short bounded render wait. Provider pacing remains enabled.

- HTTP 200: SUCCESS or PARTIAL; always inspect status, warnings and each offer.
- HTTP 400: unsupported provider or merchant, with a ScrapeResponse error envelope.
- HTTP 422: invalid request, with ApiErrorResponse {schemaVersion, errors}.
- HTTP 503: provider disabled, network/TLS/DNS/timeouts, denied access, rate limit, or browser failure.
- HTTP 502: parsing, unsupported/empty content or no usable offers.
- HTTP 500: internal failure; decode ScrapeResponse or ApiErrorResponse as applicable.

Error codes now distinguish DNS_ERROR, CONNECT_TIMEOUT, READ_TIMEOUT, TLS_ERROR, HTTP_403,
HTTP_404, HTTP_429, HTTP_5XX, REDIRECT_LOOP, BLOCK_PAGE, EMPTY_RESPONSE,
UNSUPPORTED_CONTENT_TYPE, BROWSER_NAVIGATION_FAILED, BROWSER_BLOCK_PAGE, PARSE_FAILED,
NO_OFFERS_FOUND and VALIDATION_FAILED. Legacy codes remain in OpenAPI. Bind the error code
to a **string** and handle unknown codes conservatively. Do not immediately retry denied access
or rate limits. Schedule any retries conservatively in the backend; the scraper adds no scheduler.

## Partial-provider failures

For all providers in one call, the existing aggregate endpoint is **GET /api/v1/offers**.
Optional query parameters are provider, merchant and force_refresh (snake_case in the query).
Example: `GET /api/v1/offers?provider=GYFTR&merchant=SWIGGY&force_refresh=false`.

It returns an **array of independent ScrapeResponse envelopes**, not one merged envelope.
One provider may return FAILED with errors while the other envelopes retain successful offers.
The aggregate HTTP response is 200 for these provider outcomes; inspect every array element.
A provider's PARTIAL response likewise retains usable offers and its source errors. Invalid
aggregate parameters return the same ApiErrorResponse used elsewhere (the OpenAPI declaration
was corrected and regression-tested). Allow a larger client budget for sequential aggregate
requests, or prefer separate bounded POST calls.

A failed refresh must not silently erase previously stored good offers. Apply a deliberate
freshness policy and preserve failures for diagnostics. Never replace failed live results with demo data.

## Cache and ingestion rules

A cold normal request is a miss; an identical request is a hit; forceRefresh=true fetches again.
This sequence was verified for all three providers on Windows and Docker. Cached responses
preserve original source timestamps and identities. The TTL cache is in memory, defaults to
300 seconds, and is not shared between separate CLI processes or replicas.

Before optimizer ingestion require schemaVersion=1, metadata.fixture=false and per-offer
verificationStatus=VERIFIED. AMBIGUOUS is informational; INCOMPLETE is excluded by default.
DEMO and FAILED are diagnostic classifications outside the unchanged canonical offer enum.
Apply current validity, freshness, category, payment-method and eligibility conditions separately.

Upsert by externalKey and compare contentHash. GyFTR's observed discount is payment-method
dependent; retain eligibleInstrumentTypes and terms. Yatra's separate passenger/trip/category
offers must remain separate. The scraper's existing local observation history does not replace
the backend's application persistence.

## Accepted OpenAPI baseline

The canonical ScrapedOffer schema and all three original fixture response hashes are unchanged.
The intentional OpenAPI additions are GET /api/v1/offers, optional provider-health fields and
new detailed error strings. Existing paths, required provider fields and legacy error values
remain intact. Clients must tolerate optional response fields; strict generated enum clients
must regenerate against the accepted schema.

Accepted SHA-256:
`a3b97003fc82f98f3ef5c249fa832e34ca4e7164ebc80a676f48157cd522114a`.

It is pinned in [openapi.sha256](../contracts/openapi.sha256), and contract verification checks
that exact hash. There is no unexplained mismatch. See [verification.md](verification.md) for
the final run evidence and the original-versus-accepted hash comparison.
