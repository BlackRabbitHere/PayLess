# Payment Optimizer — Phase 5

React + TypeScript, Spring Boot MVC (Java 21), FastAPI, and PostgreSQL with Flyway migrations.
Business rules remain in the existing query, eligibility, calculation, routing, and optimization modules.

## One-command startup

```sh
docker compose up
```

Open [Routewise](http://localhost:4173). The first run builds the images and applies migrations automatically.
For a detached start that waits for readiness: `docker compose up -d --build --wait`.

```text
Browser :4173 -> nginx frontend :5173 -> Spring :8080 -> FastAPI :8000 -> provider adapters
                                            |
                                       PostgreSQL :5432
```

The browser uses same-origin `/api` requests. Spring uses `SCRAPER_BASE_URL=http://scraper:8000`
and `jdbc:postgresql://postgres:5432/payment_optimizer`. Spring and FastAPI ports are internal to Docker.
PostgreSQL is exposed on localhost:15432 for development tests. Set `FRONTEND_PORT` or `POSTGRES_PORT`
in `.env` to change host ports. The defaults avoid Windows port reservations encountered during verification.
Named volumes preserve database and scraper data across ordinary container restarts.

The default stack uses labelled saved provider fixtures for deterministic development. Travel fares are still
provided by `DemoFareProvider`. To explicitly exercise live providers, set `SCRAPER_FIXTURE_DIR=` (empty),
`SCRAPER_ALLOW_FIXTURES=false`, and configure `TERMS_REVIEWED_PROVIDERS` / `PLAYWRIGHT_ENABLED` as described
in [scraper source access](scraper/docs/source-access.md). Live access can fail independently per provider.
Ordinary CI and smoke tests never request live providers.

## Smoke checkpoint

```sh
docker compose --profile smoke run --rm smoke
```

This checks frontend delivery, correlation headers, repeated Swiggy optimization, travel optimization, and
all three FastAPI fixture providers through the frontend proxy. It fails if the scraper is in live mode.
Alternatively run `python scripts/smoke.py http://localhost:4173` after starting the stack.

## Persistence and observability

Flyway owns schema changes in `backend/src/main/resources/db/migration/`; Hibernate only validates them.
The five persisted models are Merchant, MerchantAlias, Provider, Offer, and ScraperRun. Reference merchants,
aliases, and providers are seeded in V1 to match the supported application catalog.
`Offer.externalKey` maps to the unique `source_external_key` column. PostgreSQL `ON CONFLICT` upserts
observations atomically; older observations and synthetic fixtures cannot overwrite newer/live records.
Each acquisition attempt receives its own audit row, including source failures and cached scraper responses.
Offer/audit writes share a short transaction after network work. Storage failures return controlled 503 errors.
Wallet/card credentials and request bodies never enter the persistence port.

React supplies `X-Request-ID`; Spring validates or creates it, echoes it, propagates it to FastAPI, and includes
it in JSON logs and scraper-run records. FastAPI keeps its wire `requestId` unchanged and logs it separately
as `scraperRequestId`. Logs contain acquisition durations/counts, eligibility counts, candidate counts,
optimization durations, purchase amounts, merchants, providers, and partial-failure counts.

## Automated checks

```sh
# Backend: ordinary tests use saved FastAPI JSON, no PostgreSQL or provider network needed.
cd backend
./mvnw test
# Windows: .\mvnw.cmd instead of ./mvnw

# PostgreSQL repository tests + all ordinary tests; start Compose postgres first.
./mvnw -Pdatabase-tests package

cd ../frontend
npm ci
npm run check
npm run build:docker
# Requires the packaged backend and local PostgreSQL; starts fixture HTTP server + Spring + Vite.
npx playwright install chrome
npm run test:e2e

cd ../scraper
# Python 3.12+, install requirements.lock, package, and pytest/httpx (see CI workflow).
python -m pytest
```

`DATABASE_URL`, `DATABASE_USERNAME`, and `DATABASE_PASSWORD` configure standalone Spring and repository tests.
Use an isolated test database. Defaults match Compose on localhost:15432. Tests delete only rows they create.
The `test` Spring profile mocks the persistence port; `database-tests` uses real PostgreSQL and Flyway.
Backend coverage includes queries, mapping/contracts, eligibility, costs, routes, ranking, redirects,
controllers, resilience, correlation, repository concurrency/rollback, and merchant/travel integration.
Frontend checks cover architecture/model tests, hooks, components, API failures, and desktop/mobile flows.

Live tests require explicit opt-in: Maven `-Plive-scraper` plus `RUN_LIVE_SCRAPER=true`, or Python
`pytest -m live`. Configure live scraper access before using either. These commands are absent from
[ordinary CI](.github/workflows/ci.yml).

## Standalone development

Start PostgreSQL with `docker compose up -d postgres`. Start the fixture scraper with
`./scripts/start-scraper.ps1 -Profile local -Fixture`, Spring with `backend/mvnw.cmd spring-boot:run`
(from `backend`), and Vite with `npm run dev` (from `frontend`). Set frontend `VITE_API_BASE_URL`
to the standalone Spring URL. The production Spring profile requires database, scraper, and CORS configuration
and rejects fixture ingestion. The bundled database password is a local-development default.

See [Phase 5 verification](docs/phase5-verification.md), [architecture](docs/architecture.md), and
[earlier Phase 4 verification](docs/phase4-verification.md). The original scraper freeze remains intact except
for two explicitly hashed observability edits; `python scripts/verify-frozen-scraper.py` verifies that boundary.
