# PayLess branding and UI verification

Branding migration: **PASS**. Verified 20 September 2026.

Old brand: RouteWise / Route Wise / Routwise and case/hyphen variants.
New brand: **PayLess**. Description: **Smart payment route optimization**.

No commit requested or created. The rebuilt local application is available at
http://localhost:4173. All four Compose services passed their health checks.

## Pre-change inventory

The repository was clean. A case-insensitive audit of tracked files and local source,
including hidden configuration, found six matching lines across five files. Dependencies,
Git internals, compiled output and generated screenshots were excluded.

| Category | Location | Decision |
| --- | --- | --- |
| A: user-visible | Frontend shared brand configuration (name and wordmark) | Use PayLess consistently. |
| B: documentation | Root README startup link; frontend README title | Rename display copy. |
| C: technical | Wallet persistence key in walletStore; legacy demo key in model/state | Keep keys to preserve browser data compatibility. |
| C: technical documentation | Frontend README wallet storage key | Keep the exact key so documentation remains accurate. |
| D: API/database | No old-name occurrences | Preserve endpoints, JSON properties, schema and migrations. |
| E: historical/frozen | No old-name occurrences | Preserve all scraper bytes and historical verification reports. |
| F: infrastructure | No old-name occurrences | Preserve service names, artifact IDs, environment variables and DNS. |

Additional metadata inspected: index.html, favicon.svg, package.json, pom.xml,
FastAPI app metadata, pyproject.toml, Dockerfiles/Compose, nginx, Netlify and CI.
No web manifest exists. Spring has no separate OpenAPI title. FastAPI's generic
internal title belongs to a frozen file and does not contain old branding; retain it.
Only Maven's human-readable name and description change.

## Visual audit and direction

Preserve the existing purple theme and search → compare → choose workflow.
Unify the green search/result overrides with the existing tokens, increase muted
text contrast and mobile targets, make errors programmatically associated, clarify
deferred rewards, and remove raw provider codes from customer-facing results.
Keep real loading, cancellation, safe links and all server monetary values intact.

The existing SVG appears to be an R monogram. Preserve its bytes as requested,
but stop displaying it in the wordmark/browser metadata. A text-only PayLess
wordmark is sufficient; a replacement favicon remains a separate asset decision.

## UI/UX improvements

| Area | Result |
| --- | --- |
| Branding | Shared name, tagline and description; canonical wordmark, browser title, application metadata, README titles and Maven display metadata. |
| Navigation | Home/Travel/Wallet/Recent remain available on mobile; logo returns Home; route changes focus the main content; skip link, modal Escape and focus restoration verified. |
| Home | Clear value proposition, supported demo categories/providers, how-it-works copy and accurate privacy note. Mobile search appears before the explanation. |
| Search | Visible label, placeholder, hint, working Swiggy example chips and a travel link. Wallet selection count and empty-wallet guidance. |
| Wallet | Clear add-payment-method CTA, useful empty state, existing metadata-only form, more usable removal targets and tablet layout. Persistence keys remain compatible. |
| Results | Recommendation precedes fare comparison and alternatives; separate Pay Now, Effective Cost and savings surfaces; server monetary values remain untouched. |
| Payment steps | Numbered instructions, provider-specific booking/continuation labels, existing allowlisted URLs and opener protection. |
| Offer provenance | Source, status, exact last-check timestamp or explicit missing timestamp, terms and visible demo labeling. Stale status and deferred-reward presentation have regression coverage. |
| Travel | Labeled stacked mobile fields, associated error feedback, separate fare/payment savings/effective cost, friendly unsupported-route guidance. |
| Responsive | Home, wallet, merchant results, travel form and travel results checked at 375, 430, 768, 1024 and 1440 pixels. Comparison table scrolls within its own keyboard-focusable region. |
| Accessibility | Stronger muted text and focus colors, semantic table headers, form-error associations, keyboard navigation, persistent heading hierarchy and reduced-motion rules. |
| Loading | Existing real request state and cancellation retained; submission disables while checking offers; input and wallet changes still cancel stale requests. |
| Errors | Friendly known API errors and safe generic fallbacks; unknown exception details never reach the UI. Provider summaries omit raw codes/identifiers. Direct-payment fallback, no-discount and empty-result states remain useful. |

## Tests and verification

| Check | Result |
| --- | --- |
| `npm run check` | PASS: TypeScript, ESLint, 19 model/architecture/branding tests and 11 React/API/component tests. |
| `npm run build` | PASS: production build; no bundle warnings. JS 309.90 kB / 98.18 kB gzip; CSS 66.09 kB / 14.26 kB gzip. |
| Docker frontend build | PASS: existing `npm run build:docker` completed in the image build. |
| `mvnw.cmd -B -ntp -Pdatabase-tests package` | PASS: 122 tests, zero failures/errors/skips, including PostgreSQL persistence and integration tests. |
| `python scripts/verify-frozen-scraper.py` | PASS: all 105 files match the existing baseline and its two previously approved observability overrides. No new overrides. |
| Scraper offline `python -m pytest -p no:cacheprovider` | PASS: 133 tests; five live/browser tests intentionally deselected by the existing configuration. Run against read-only workspace source in a temporary Python 3.12 scraper container because the host has Python 3.11 and no pytest. Only test dependencies installed in the disposable container. |
| `npm run test:e2e` | PASS: 20 desktop/mobile tests, final clean exit in 55.4 seconds. Covers safe provider popups, exact money, wallet persistence/add/remove/empty state, keyboard navigation, five viewport widths, cancellation/retry, provider failures, errors and deep links. |
| `docker compose up -d --build --wait` | PASS: full stack rebuilt and healthy. Existing volumes retained. |
| `docker compose --profile smoke run --rm smoke` | PASS: frontend, correlation, merchant repeat ingestion, travel and all fixture providers. |
| Production browser checks against Compose | PASS: real frontend → Spring → FastAPI → PostgreSQL flows at 1440 and 375 pixels; no page errors or document overflow. Swiggy Pay Now ₹487.50; demo travel Pay Now ₹5,459. Direct wallet/travel deep links loaded through nginx. |
| Final branding search | PASS: no unexplained display branding. Intentional matches listed below. |
| `git diff --check` | PASS: no whitespace errors. |

No dependencies, API contracts, optimization/ranking calculations, database migrations,
scraper code/fixtures, redirect security, deployment configuration or CI were changed.
Netlify and nginx SPA fallbacks were inspected and preserved.

## Technical identifiers and remaining old-brand references

| Location | Remaining reference and reason |
| --- | --- |
| `frontend/src/features/wallet/controller/walletStore.ts:9` | `routewise-wallet-v2`: existing wallet persistence key; changing it would lose access to stored wallets. |
| `frontend/src/features/optimization/model/state.ts:8` | `routewise-demo-v1`: legacy prototype compatibility key. |
| `frontend/README.md:10` | `routewise-wallet-v2`: documents the actual storage key. |
| `frontend/tests/branding.test.ts:9` | Old-name detection regex, intentionally needed to reject future regressions. |
| `frontend/tests/branding.test.ts:12` and `:13` | The two exact preserved keys above; exemptions are restricted to one string in each specific file. |
| `frontend/tests/e2e/branding-responsive.spec.ts:5` | Old-name detection regex used to reject visible browser branding. |
| This report | The old-brand inventory and exact compatibility references are intentional audit evidence. |

Other stable identifiers retain their current values: npm package `payment-optimizer-frontend`,
Maven artifact `payment-optimizer`, Java package `com.paymentoptimizer`, Python distribution
`payment-scraper` and module `payment_scraper`, database `payment_optimizer`, Compose project,
service/DNS/volume names, environment variables and API paths. Renaming them offers no user-facing
benefit and would introduce unnecessary build, storage or deployment risk.

## Files changed

```text
README.md
backend/pom.xml
docs/payless-verification.md
frontend/README.md
frontend/index.html
frontend/src/app/config/brand.ts
frontend/src/app/router/AppRouter.tsx
frontend/src/features/optimization/view/HomePage.tsx
frontend/src/features/optimization/view/ResultsPage.tsx
frontend/src/features/optimization/view/SearchBox.tsx
frontend/src/features/optimization/view/SearchState.tsx
frontend/src/features/travel/view/TravelPage.tsx
frontend/src/features/wallet/view/WalletPage.tsx
frontend/src/shared/api/httpClient.ts
frontend/src/shared/components/Header.tsx
frontend/src/shared/components/UI.tsx
frontend/src/styles.css
frontend/tests/branding.test.ts
frontend/tests/e2e/branding-responsive.spec.ts
frontend/tests/e2e/prototype.spec.ts
frontend/tests/e2e/service-status.spec.ts
frontend/tests/react/RouteCard.test.tsx
frontend/tests/react/httpClient.test.ts
```

## Regressions found and resolved

- Mobile screenshots exposed the off-screen skip link; its unfocused state is now
  explicitly invisible while keyboard access remains verified.
- Mobile explanatory content pushed the query too far down; the search now comes first.
- An initial generic CTA mapping called a food checkout a booking; labels now map only
  the known merchant actions, with coverage for Swiggy continuation and travel booking.
- The first sandboxed Windows Playwright run passed its scenarios but stalled during
  server teardown. Only its identified process tree was terminated. The final permitted
  run completed normally with all 20 tests passing. No test-server configuration changed.
- An ad hoc production screenshot probe initially used an overly exact heading selector;
  correcting the selector produced passing desktop/mobile production checks.

No unresolved functional regression was found in the checked flows.

## Known limitations and manual review

- Existing demo scope remains: selected merchants, synthetic offers and Delhi ↔ Mumbai
  fares. Live-provider acquisition was not tested or implied to work by these checks.
- The old R-shaped SVG is preserved but unused. No replacement favicon was introduced.
- This is not a formal accessibility certification; keyboard/focus checks and visual
  inspection were performed in Chrome. Screen-reader and Safari/Firefox review remain useful.
- Scraper tests emitted two upstream deprecation warnings; dependencies were not changed.
- Generated PNGs remain local, ignored artifacts in `frontend/test-results/`. Review the
  `payless-*` images for all five widths and loading/error/empty/unavailable states, and
  `compose-*` images for production Home, Wallet, merchant results, travel and travel results.
  Prioritize the 375px mobile payment instructions and long provider terms in a human demo review.
