# Architecture

Provider configuration selects curated public HTTPS URLs. HTTP is attempted first using a
persistent Requests session, verified TLS, separate connect/read timeouts, bounded responses
and validated redirects. The default retry count is zero. The configurable per-host interval
is three seconds; use one worker/replica because pacing and the TTL HTTP cache are process-local.

Activation uses independent PROVIDER_*_ENABLED settings. Robots rules are fetched, cached,
snapshotted and reported, including disallows and unavailable/unrecognized rules. They do not
disable providers. TERMS_REVIEWED_PROVIDERS is retained as audit metadata. Neither is proof of
legal permission. Exact provider/action domain checks remain enforced.

READ_TIMEOUT, BLOCK_PAGE, empty/static JS shells or absent required structures can trigger one
ordinary Playwright Chromium attempt. HTTP 403/429, TLS and DNS failures do not trigger retries
through a different identity. Chromium uses native networking and a fresh context, without
stealth, custom fingerprints, proxy rotation, login, or challenge interaction. Main navigation
is restricted to the provider allowlist; public HTTPS resources may use CDN hosts. Navigation,
selector wait, request count and captured size are bounded. ExitStack always closes page,
context, browser and Playwright. No indefinite networkidle wait is used.

Successful source bodies and diagnostic error bodies are saved before parsing. HTTP snapshots
hold raw response bytes; browser snapshots hold rendered DOM and optional public same-provider
JSON responses. Sidecars include URLs, redirect chain, timing, requestId, status, encoding,
byte count, SHA-256 and HTTP/PLAYWRIGHT identity. Files are created without overwriting an
existing snapshot; retention still prunes old captures. Regression fixtures have a separate,
permanent provenance record and a hash of the sanitized bytes.

Each provider retains its config.py, parser.py and scraper.py adapter. Public parsers use:
- Yatra: semantic heading/offer lists and the category/minimum table.
- GyFTR: displayed denomination/price labels and embedded Next.js product/payment-method data.
- EaseMyTrip: semantic coupon, booking-period and benefit/condition labels.

The parsers return source strings in RawOffer. Normalization uses Decimal, explicit INR values
and India calendar dates converted to UTC. Pydantic validates the unchanged ScrapedOffer schema.
Sanity validation compares voucher face/price/percentage, checks dates, and preserves discrepancy
values in warnings. Unknowns remain null/UNKNOWN; an unspecified minimum is never invented.

VERIFIED describes internally consistent source observations. AMBIGUOUS stays informational;
INCOMPLETE is excluded. Fixture envelopes retain metadata.fixture=true and a FIXTURE_DATA warning.
Diagnostics classify fixture observations as DEMO and unsuccessful scrapes as FAILED without
altering the established canonical verification enum. Production consumers must require both
metadata.fixture=false and verificationStatus=VERIFIED, then apply freshness and eligibility policy.

Deduplication retains existing externalKey and contentHash rules. SQLite observation history
upserts by externalKey and stores firstSeenAt, lastSeenAt, lastVerifiedAt and source hash outside
the wire contract. Cached source timestamps remain unchanged; stale observations cannot replace
newer rows. The HTTP cache remains in memory and is not shared between CLI processes.

CLI and FastAPI call the same service. GET /api/v1/offers returns independent provider envelopes,
so one outage does not remove other results. Provider health separates configured capability,
activation, reachability and observed live verification. Health persists locally; lastCheckedAt
makes the observation time explicit. It is not a continuous monitor.

The service does not calculate routes, effective cost, eligibility or payment recommendations.
Spring Boot can ingest canonical JSON, upsert by externalKey and retain source timestamps.
