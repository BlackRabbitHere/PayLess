# Phase 5 verification

Verified on 2026-09-20 with Java 21, PostgreSQL 17 in Docker, Python 3.12 in Docker, and Chrome desktop/mobile emulation.

| Check | Result |
| --- | --- |
| Backend ordinary + PostgreSQL tests (`mvnw -Pdatabase-tests package`) | 122 passed |
| PostgreSQL repository tests within that suite | 6 passed: migration/reference data/indexes, round-trip money, repeat upsert, stale verification downgrade, fixture/live protection, concurrent upserts, failed-run audit and transaction rollback |
| Frontend type checking and ESLint | Passed |
| Existing frontend unit/architecture tests | 18 passed |
| React hooks, API errors/correlation, and component tests | 8 passed |
| Desktop/mobile browser flows | 14 passed |
| Offline FastAPI tests | 133 passed; 5 live/browser tests deselected |
| Docker images + health dependencies | All four services healthy |
| Full nginx -> Spring -> FastAPI merchant/travel smoke | Passed |
| PostgreSQL restart | All three offers retained; backend reconnected; merchant/travel smoke passed again |
| PostgreSQL inspection after repeat ingestion | One persisted offer for each of GYFTR, YATRA, EASEMYTRIP; multiple audit rows |
| Cross-service structured log inspection | Same requestId in scraper, acquisition, routing, optimization events; separate scraperRequestId retained |
| Frozen baseline + two explicit correlation overrides | 105 files verified |
| Frontend dependency audit after patched Vitest update | 0 vulnerabilities reported |

## Reproduce

```sh
docker compose up -d --build --wait
docker compose --profile smoke run --rm smoke
```

Open http://localhost:4173. PostgreSQL is available for local Java tests on localhost:15432.
Spring's container uses `http://scraper:8000` and `jdbc:postgresql://postgres:5432/payment_optimizer`.
Windows reserved ports 5173 and 5432 here; only the host mappings changed. An existing unrelated scraper
on host port 8000 was left running. The stack's Spring/FastAPI ports remain internal.

```sh
cd backend
./mvnw -Pdatabase-tests package
cd ../frontend
npm ci
npm run check
npx playwright install chrome
npm run test:e2e
```

On Windows use `mvnw.cmd`. Browser tests launch their own fixture-response server, Spring process, and Vite;
they use the local PostgreSQL instance. Repository tests generate unique keys and clean only their own rows.
For an isolated test database, override DATABASE_URL / DATABASE_USERNAME / DATABASE_PASSWORD.
Default `mvnw test` excludes repository and live-scraper tags and mocks the persistence port in HTTP tests.

Offline scraper checks can also run in a disposable container:

```sh
docker compose run --rm --no-deps --user root -v ./scraper/tests:/app/tests:ro scraper sh -c 'pip install pytest httpx && python -m pytest tests'
```

Ordinary CI is defined in `.github/workflows/ci.yml`; it runs the PostgreSQL, frontend, scraper, browser,
and Compose fixture smoke checks. It does not invoke live provider tests.

## Behavior and limits

- Flyway V1 owns the five tables and reference catalog; V2 adds access-pattern indexes. Hibernate validates all five mappings.
- Offers are atomically upserted by source_external_key. All mapped observations are stored before eligibility filtering.
- Older observations cannot replace newer ones; fixtures cannot replace live records. A live record can supersede a fixture.
- Offer writes and the attempt audit commit together. Network calls happen before the database transaction.
- Source failures produce an audit and preserve direct-payment fallback. Storage failures return a controlled 503.
- Reference merchants/aliases/providers are versioned seed data matching the supported application catalog; this phase adds no catalog admin UI.
- The application still acquires current offers for optimization. It does not silently recommend stale database offers during a scraper outage.
- Request IDs are bounded/validated, echoed, propagated, and cleaned after each request. No query text, wallet/card secrets, or request bodies are persisted/logged by the new code.
- Browser tests cover Swiggy, travel, wallet changes, validation, partial/total source failures, loading/cancellation, retry, and redirect safety.
- Docker/CI fixtures are synthetic and visibly labelled. Travel fares remain demo fares. Live providers were not exercised during this verification.
- The scraper wire contract and provider logic remain frozen. Only HTTP middleware and the JSON formatter changed; their LF-normalized hashes are audited separately from the original manifest.

Local raw verification output is under ignored `data/verification/phase5-*.log`; this document records the portable results.
