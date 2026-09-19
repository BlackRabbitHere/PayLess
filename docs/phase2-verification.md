# Phase 2 verification — 2026-09-19

The mandatory live boundary passed before any optimizer work:

```text
I am paying 500 rs on swigy
  -> PurchaseContext(SWIGGY, FOOD_DELIVERY, 500.00, 0.96)
  -> OfferAcquisitionService -> GYFTR / SWIGGY
  -> POST /api/v1/scrape
  -> ScraperResponse / ScrapedOfferDto
  -> ScraperOfferMapper -> 7 genuine Offer objects
```

## Frozen contract inspection

Read the accepted OpenAPI, serialization schema, all provider contract fixtures,
genuine GyFTR observation/envelope, API routes, provider-status schema and integration guide.
The running FastAPI `/openapi.json`, `/api/v1/providers` and `/api/v1/schema/offers` were also inspected.
The live offer schema matched `scraper/contracts/scraped_offer.schema.json` structurally.

- Supported pairs: GYFTR/SWIGGY, YATRA/YATRA, EASEMYTRIP/EASEMYTRIP.
- Money is decimal strings on the wire and BigDecimal in Java. Percentage precision is retained.
- Offer/envelope timestamps bind to Instant. Provider diagnostic dates remain nullable strings,
  matching their OpenAPI types rather than inventing stricter requirements.
- HTTP 200 carries SUCCESS/PARTIAL; failures use ScrapeResponse or the smaller ApiErrorResponse.
  Error codes remain strings; retryability is preserved. No automatic retries are added.
- `forceRefresh=false` uses the scraper cache; `true` bypasses it. Cache hits preserve source observation times.
- Optional provider diagnostics do not gate a first scrape: `liveReady=false` can simply mean no successful observation yet.
- Nulls, UNKNOWN values and empty eligibility lists remain unknown information.

`python scripts/verify-frozen-scraper.py` passed: all 105 frozen files retain their original SHA-256 hashes.
No FastAPI source, schema, fixtures or provider implementation was changed.

## Genuine integration evidence

The live JUnit test starts Spring on a random port and calls its development acquisition endpoint over HTTP.
Spring then calls the running frozen FastAPI service at `http://127.0.0.1:8000`.
Fixture acceptance is explicitly disabled for this test.

The checkpoint returned SUCCESS, `fixture=false`, and seven VERIFIED GyFTR/Swiggy offers.
One actual observation was a ₹150.00 voucher priced at ₹146.25 with a 2.50 percentage discount,
with its source terms, UPI/WALLET restrictions and `https://www.gyftr.com/swiggy-gv` source URL preserved.
These values are evidence, not hardcoded expectations in the live test.
The first successful checkpoint's request ID was `ce654211-f379-4a0a-8d87-ff637a651144`;
its source observation time was `2026-09-19T08:11:54.811125Z`.

A follow-up Java client call returned `cacheHit=true` with the same source timestamp.
A forced refresh returned `cacheHit=false` and a newer timestamp. Both remained non-fixture responses.

Each successful run refreshes these local evidence files (ignored by Git):

- `data/verification/phase2/spring-acquisition.json`: PurchaseContext and mapped domain offers.
- `data/verification/phase2/scraper-response.json`: the Java DTO after genuine forced refresh.
- `data/verification/phase2/provider-statuses.json`: deserialized provider diagnostics.

The evidence files are Java serialization, not byte-for-byte HTTP captures; BigDecimal values appear as JSON numbers there.
The frozen scraper continues to send decimal strings.

## Repeat the checks

Offline contract/query/architecture suite, from `backend/`:

```powershell
./mvnw.cmd -B -ntp test
```

58 tests run without provider network access. The additional live checkpoint is skipped unless opted in.
Coverage includes all three frozen provider contracts, money/null/time fidelity, query matching and ambiguity,
request method/path/body, provider isolation, both error envelope formats, partial results,
malformed commercial data, production fixture rejection, timeouts and module boundaries.

With the frozen scraper already running in live mode, from the repository root:

```powershell
./scripts/verify-phase2.ps1
```

Or run all 59 checks together from `backend/`:

```powershell
$env:RUN_LIVE_SCRAPER = 'true'
./mvnw.cmd -B -ntp test
Remove-Item Env:RUN_LIVE_SCRAPER
```

The live test uses a 180-second scraper read timeout. Normal tests use an isolated controlled HTTP server.
The verification launcher was syntax-checked; its Maven invocation was exercised directly.

An attempted `clean verify` was blocked at the clean step by an existing process holding
`backend/target/payment-optimizer-0.0.1-SNAPSHOT.jar`. Compilation and all test checks were subsequently run
with `test`; the running application was not stopped. A new packaged JAR was not verified.

## Scope remaining after this checkpoint

No optimizer, card evaluation, savings calculation, route ranking, persistence or production refresh scheduler was added.
The synchronous acquisition endpoint is a development checkpoint and is absent in production.
Acquired VERIFIED offers still need freshness, validity, payment-method and eligibility policies before optimization.
The query module supports the three frozen merchants and numeric INR amounts; unsupported or ambiguous inputs return 400
with a controlled clarification code. Confidence values represent deterministic matching quality, not statistical probabilities.
