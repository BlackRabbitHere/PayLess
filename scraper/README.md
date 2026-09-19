# Payment Offer Scraper

Independent Python 3.12+ service for collecting public payment offers. The API and CLI
share one deterministic pipeline and one versioned Pydantic contract. Money uses
`Decimal` internally and decimal strings over JSON; times are UTC.

**Current readiness (2026-09-19):** Yatra, GyFTR and EaseMyTrip return genuine
normalized offers through the CLI, FastAPI and Docker. Public response snapshots
and sanitized regression fixtures have been captured for all three providers.
See [verification evidence and remaining gaps](docs/verification.md).

The service does not implement user accounts, card eligibility, ranking,
an optimizer, a frontend, or a Spring backend.
Local SQLite observations preserve offer identity and first/last observation times.

## Setup

Run these commands from `scraper/`:

```sh
python --version  # 3.12 or newer
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[test]"
cp .env.example .env  # PowerShell: Copy-Item .env.example .env
```

For a reproducible environment, install uv and run `uv sync --frozen --extra test`.
`uv.lock` captures the tested dependency resolution; Docker uses the hash-verified
runtime export in `requirements.lock`.

Playwright is installed as a dependency. All three providers support ordinary Chromium
fallback. Install its runtime for browser acquisition:

```sh
python -m playwright install chromium
# Linux CI: python -m playwright install --with-deps chromium
```

## Run offline, with clearly labeled fixture data

```sh
python -m payment_scraper.cli scrape --provider gyftr --merchant swiggy --fixture-dir tests/fixtures --output data/normalized/offers.json
```

Add `--json` for the canonical envelope on stdout; logs go to stderr. Exit codes:
0 success, 2 partial (review warnings/errors), 1 failed. Fixtures are never substituted
for a failed live request. API fixture mode is a server-side development setting:

```powershell
$env:FIXTURE_DIR = 'tests/fixtures'
uvicorn payment_scraper.api.app:app --reload
```

On Linux/macOS: `FIXTURE_DIR=tests/fixtures uvicorn payment_scraper.api.app:app --reload`.
Then use `/health`, `/docs`, `/openapi.json` and:

```sh
curl -X POST http://localhost:8000/api/v1/scrape -H "Content-Type: application/json" -d '{"provider":"GYFTR","merchant":"SWIGGY","forceRefresh":false}'
```

PowerShell alternative:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/scrape -Method Post -ContentType application/json -Body '{"provider":"GYFTR","merchant":"SWIGGY"}'
```

Every fixture response contains `metadata.fixture=true`, `fetchMethod=FIXTURE`, and a
`FIXTURE_DATA` warning; `/health` reports fixture mode. Production rejects this mode.

## Live operation

Activation uses `PROVIDER_YATRA_ENABLED`, `PROVIDER_GYFTR_ENABLED`, and
`PROVIDER_EASEMYTRIP_ENABLED` (default true). `PLAYWRIGHT_ENABLED=true` enables
the browser fallback. Robots observations and `TERMS_REVIEWED_PROVIDERS` are audit
metadata, not execution gates or evidence of legal permission. Clear `FIXTURE_DIR`, then:

```sh
python -m payment_scraper.cli scrape --provider yatra --merchant yatra --force-refresh --json
uvicorn payment_scraper.api.app:app --host 127.0.0.1 --port 8000 --workers 1
```

Authentication/anti-bot blocking, network failures and unknown HTML
produce structured errors. A new authorized HTML capture may require provider-specific
selector updates. No production prices are hardcoded.

Policy-only review: `python tools/review_source_access.py --provider yatra`.
Use
`python tools/probe_provider.py --provider yatra --merchant yatra` to verify HTTP
and save raw snapshots before changing parser selectors. Neither tool enables providers.

Cache and domain pacing state belong to one service process. Two separate CLI
invocations start with empty caches; there is no persistent CLI cache or distributed
rate limiter. Within a running API worker, normal scrapes reuse the HTTP cache;
`forceRefresh=true` bypasses it. Cached observations keep their original timestamps.

## Tests

```sh
python -m compileall src
pytest
pytest tests/unit
pytest tests/parsers
pytest tests/contract
pytest -m live  # explicit network opt-in; skips disabled providers
pytest -m browser  # actual Chromium, controlled transport; independent of provider access
ruff check src tests
```

Ordinary tests are offline and exclude live and browser tests by default. They cover parsing,
normalization, validation, JSON/OpenAPI, caching, retries, redirect restrictions,
rate limiting, robots rules, snapshot retention, and fixture API/CLI execution.

On this Windows machine Chromium uses a project-local cache because the default
user cache has a filesystem link loop:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) 'data\browsers'
python -m playwright install chromium
python -m pytest -m browser -vv -p no:cacheprovider
```

`python tools/smoke_server.py --provider YATRA --merchant YATRA` starts real Uvicorn
and tests health, Swagger, OpenAPI and **fixture** scraping. Add `--live` only after
activation to require real HTTP; failures remain failures and are saved under
`data/verification/`. The subprocess always shuts down after the check.

## Docker

```sh
docker compose up --build
curl http://localhost:8000/health
```

The image installs Chromium only, runs as a non-root user, and publishes the API on
loopback port 8000. A named volume stores snapshots and observation history.
Provider activation is separate from source audit metadata.
The local development machine needs a running Docker daemon to build/run it.

## Architecture and extension

Registry → provider configuration → reusable HTTP / Chromium → raw snapshot →
provider parser → normalizer → Pydantic validation → sanity verification → identity
and deduplication → versioned response → CLI/REST.

Adding a source means adding a provider package with config, pure parser and adapter,
then registering it in `default_registry()`. Keep selectors within that package.
Add an authorized fixture, parser/contract tests and a source-review record before
claiming live readiness. Browser fallback additionally requires explicit provider
support and a bounded selector wait. There is no CAPTCHA solving, authentication
bypass, stealth, proxy rotation, or rate-limit evasion.

`GET /api/v1/offers?provider=GYFTR&merchant=SWIGGY` returns per-provider scrape
envelopes; omitting filters aggregates all configured providers with isolated errors.
`GET /api/v1/providers` reports enabled, transport/parser readiness and observed
live health. Only non-fixture VERIFIED observations should enter production ingestion.
The unchanged canonical enum remains VERIFIED/AMBIGUOUS/INCOMPLETE; DEMO and FAILED
are diagnostic classifications outside the offer schema.

See [architecture](docs/architecture.md), [API contract](docs/api-contract.md), and
[future Spring integration](docs/spring-boot-integration.md). The ingestion API should
run on a trusted internal network behind deployment authentication and request limits;
it is intended for background refresh, not user search requests.
