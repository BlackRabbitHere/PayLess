# PayLess React integration — Phase 5

Home submits the purchase sentence and selected wallet metadata to Spring at `POST /api/optimize/query`.
Travel submits origin, destination, departure date, passengers and wallet to `POST /api/travel/optimize`.
The browser never calls FastAPI. Spring owns query understanding, eligibility, route generation, money and ranking.

- `features/optimization/model/contracts.ts` mirrors Spring request, response and domain records.
- `useOptimizationController` owns query, selection, submit, loading, response, error and reset. Its feature provider shares this in-memory state between the forms and results routes.
- `optimizationApi.optimize()` and `travelApi.optimize()` use the shared Spring HTTP client.
- Zustand persists only wallet metadata in `routewise-wallet-v2`. Recent searches are session-only; responses are never persisted. Reloading results asks for a fresh search.
- Wallet or input changes cancel pending requests and discard stale results. Reset aborts the request.
- Views render server costs, steps, sources, terms, eligibility exclusions and partial/total provider failures. Links are checked against approved HTTPS hosts and open with opener protection.
- The old demo model fixtures remain for historical unit tests; active search and result controllers do not use their financial calculations.

## Run and verify

Use the four-service Docker startup in the root README. Then open Home for Swiggy or Travel for Delhi–Mumbai.
The travel fare source is explicitly synthetic and supports Delhi ↔ Mumbai; other listed city pairs return an empty result.
The committed travel offers have restrictions that the eligibility engine conservatively excludes. No discount is invented.

```powershell
cd ../backend
./mvnw.cmd -B -ntp verify
cd ../frontend
npm run check
npm run build:docker
npm run test:e2e
```

The browser suite starts an isolated real Spring jar on 18080, Vite on 15173 and a test-only scraper contract replay server on 18000.
Start PostgreSQL with `docker compose up -d postgres`, then build the Spring jar first. Google Chrome must be installed. Set E2E_PORT to change the browser port.
The tests use committed synthetic wire fixtures at the Spring → scraper boundary; these are not live-provider checks.
They cover both browser scenarios, safe new-tab actions, mobile layouts, validation, empty fares, acquisition failures,
API errors, cancellation, retry, and wallet persistence. Browser traffic never reaches the replay service.

Spring response money comes from BigDecimal JSON numbers. React formats it without recomputing benefits.
The HTTP timeout is 75 seconds, allowing the two default 30-second travel provider budgets.


The client sends a fresh `X-Request-ID` with each request. Docker uses the same-origin nginx proxy; standalone Vite uses `VITE_API_BASE_URL`.
`npm run check` runs type checking, ESLint, model/architecture tests, and React hook/component/API tests.
