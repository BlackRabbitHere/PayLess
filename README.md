# Payment Optimizer — Phase 3

React + TypeScript + Vite + Tailwind, Spring Boot MVC (Java 21), and the frozen FastAPI scraper.
The existing Routewise demo UI is retained and refactored into feature modules. No PostgreSQL or backend persistence is introduced.

```text
payment-optimizer/          # this workspace root
├── frontend/
├── backend/
├── scraper/               # frozen source, unchanged
├── data/                  # fixtures and source hash manifest
├── docs/
├── scripts/
├── docker-compose.yml
└── README.md
```

## Local startup (three terminals)

Requires Java 21, Node.js 22.12+ (Node 24 also works), and Python 3.12+. Maven is provided through the wrapper.
For a fresh checkout, install frontend and scraper dependencies once:

```powershell
cd frontend
npm ci
cd ..
py -3.12 -m venv scraper/.venv
./scraper/.venv/Scripts/python.exe -m pip install --require-hashes -r scraper/requirements.lock
```

The launcher sets PYTHONPATH to the frozen source; an editable install is unnecessary.
On this existing Windows workspace it can reuse the original Python 3.12 virtual environment under ignored `Scrapper/`.

Terminal 1, from the repository root:

```powershell
./scripts/start-scraper.ps1 -Profile local -Fixture
```

Terminal 2:

```powershell
cd backend
./mvnw.cmd spring-boot:run
```

Terminal 3:

```powershell
cd frontend
npm run dev
```

Open [React](http://localhost:5173), [Spring health](http://localhost:8080/actuator/health),
[FastAPI health](http://localhost:8000/health), and [connection checks](http://localhost:5173/system).
The local scraper fixture mode is deterministic and clearly labelled. Omit `-Fixture` to use the frozen live acquisition path;
live behavior depends on provider availability and existing scraper configuration.

On macOS/Linux use `./mvnw`, `python3.12 -m venv scraper/.venv`, and `scraper/.venv/bin/python`.
Launch the scraper from its directory with
`APP_ENV=local FIXTURE_DIR=tests/fixtures PYTHONPATH=src .venv/bin/python -m uvicorn payment_scraper.api.app:app --host 127.0.0.1 --port 8000`.

## Environment profiles

| Profile | Spring | React | Scraper |
|---|---|---|---|
| local | default; allows labelled fixtures | `npm run dev`, development mode | launcher `-Profile local -Fixture` |
| test | `SPRING_PROFILES_ACTIVE=test`; tests use isolated HTTP server | `npm run dev:test` | launcher `-Profile test -Fixture` |
| docker | Compose selects docker; service DNS | `build:docker`, browser reaches localhost:8080 | Compose fixture mount |
| production | explicit URL and CORS required; fixtures rejected; probe endpoint absent | `npm run build`, same-origin API by default | `APP_ENV=production`, no fixture directory |

Vite reserves `local` as an environment-file suffix, so its development mode represents the local profile.
The committed frontend `.env` sets `VITE_API_BASE_URL=http://localhost:8080`.
Copy `frontend/.env.example` to `frontend/.env.local` for local overrides; clear that override before a production build
or set VITE_API_BASE_URL explicitly at build time. VITE_* values are public and must never hold secrets.
Vite reads API settings at startup/build time; restart after changes.

Spring configuration:

```yaml
scraper:
  base-url: ${SCRAPER_BASE_URL:http://127.0.0.1:8000}
  connect-timeout: ${SCRAPER_CONNECT_TIMEOUT:5s}
  read-timeout: ${SCRAPER_READ_TIMEOUT:30s}
```

For an override in PowerShell, set `$env:SCRAPER_BASE_URL='http://127.0.0.1:8000'` before starting Spring.
Production also requires `CORS_ALLOWED_ORIGINS` and `SPRING_PROFILES_ACTIVE=production`.
The root `.env.example` is for Compose; Spring does not automatically load dotenv files.

## Docker local environment

```sh
docker compose up --build
docker compose down
```

The same three host ports are exposed. Compose defaults to explicit scraper fixtures and backend fixture acceptance.
No database service exists. Browser API URLs use localhost, while Spring uses `http://scraper:8000`.
Docker is a local verification setup, not a production deployment definition.
For production builds, provide deployment-specific VITE_API_BASE_URL and a same-origin `/api` reverse proxy if the value is empty.

## Verification

```powershell
python scripts/verify-frozen-scraper.py
./scripts/verify-phase1.ps1
cd backend
./mvnw.cmd -B -ntp verify
cd ../frontend
npm test
npm run build
npm run test:e2e
```

The smoke script expects all three local services running and checks all three provider mappings.
The browser suite uses installed Google Chrome and starts/reuses Vite on 5173.
The backend tests start a controlled HTTP server and do not depend on internet providers.

See [architecture](docs/architecture.md) for module boundaries and deferred responsibilities,
and [verification](docs/phase1-verification.md) for completed checks.

## Phase 2: query to genuine offers

Spring now parses purchase sentences and acquires domain offers from the frozen scraper:

```text
"I am paying 500 rs on swigy"
  -> SWIGGY / FOOD_DELIVERY / INR 500.00 / confidence 0.96
  -> OfferAcquisitionService -> GYFTR only
  -> ScraperClient -> FastAPI -> ScrapedOfferDto -> ScraperOfferMapper -> List<Offer>
```

The development endpoint is `POST /api/v1/offers/acquisition-check` with
`{"sentence":"I am paying 500 rs on swigy","forceRefresh":true}`.
Set `SCRAPER_READ_TIMEOUT=180s` when running this checkpoint against live providers.
The endpoint is absent in production. It does not rank offers or calculate savings.

To run the genuine integration check against FastAPI on port 8000 (live mode):

```powershell
./scripts/verify-phase2.ps1
```

This starts an isolated Spring test server, rejects fixtures, checks the actual GyFTR response,
and verifies cache/force-refresh semantics. See [Phase 2 verification](docs/phase2-verification.md).

## Phase 3: optimization engine

`POST /api/optimize/query` now runs query understanding, offer acquisition, eligibility, route generation,
decimal cost calculation, deterministic ranking, actionable steps and redirect validation inside Spring.
The optional wallet contains payment metadata only. Responses distinguish pay-now from effective cost and include
both winning routes, alternatives, source metadata, eligibility reasons and warnings. Provider outages retain direct routes.

```powershell
curl.exe --fail-with-body -H "Content-Type: application/json" --data-binary "@docs/phase3-request.json" http://localhost:8080/api/optimize/query
```

See [Phase 3 API and verification](docs/phase3-verification.md) for the request contract, reproducible checkpoint and supported business rules.
The React demo is unchanged.
