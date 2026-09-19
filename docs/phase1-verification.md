# Final Phase 1 verification

Verified on 2026-09-19. Phase 1 is complete. No Phase 2 functionality was added.

## Running services

- React/Vite: http://localhost:4173; main page rendered successfully in Chrome.
- Spring Boot: http://localhost:8080; actuator health reports `UP`.
- FastAPI: http://localhost:8000; health reports `ok`, schema 1, live mode.
- `/api/v1/system/status` reports `backend: UP` and `scraper.status: UP`.
- An unmocked Chrome check used the React connection screen to call Spring and
  retrieve scraper status and seven mapped GyFTR observations successfully.
  No browser console errors or page errors occurred.

## Windows port reservation

`npm run dev -- --port 5173 --strictPort` failed with `listen EACCES`.
`netsh interface ipv4 show excludedportrange protocol=tcp` confirmed that Windows
reserves TCP ports 5141-5240, including 5173. This is an OS port-reservation issue,
not an application startup defect. The existing Vite server on 4173 was reused.

Use `npm run dev -- --port 4173 --strictPort`, set `$env:E2E_PORT='4173'` for
Playwright, and pass `-FrontendUrl http://localhost:4173` to the smoke script.
The local Spring profile now permits both localhost and 127.0.0.1 origins on
4173 as well as 5173; an explicit `CORS_ALLOWED_ORIGINS` still takes precedence.

## Checks

| Check | Final result |
| --- | --- |
| Backend `./mvnw.cmd -B -ntp verify` | PASS: 17 tests, zero failures/errors/skips; JAR packaged |
| Frontend `npm test` | PASS: 18 tests |
| Frontend `npm run build` | PASS: TypeScript and Vite production build |
| Existing `npm run test:e2e` with `E2E_PORT=4173` | PASS: all 16 desktop/mobile tests |
| `./scripts/verify-phase1.ps1 -FrontendUrl http://localhost:4173` | PASS: all services; GyFTR 7, Yatra 8, EaseMyTrip 1 mapped observations, all non-fixture |
| Unmocked browser check | PASS: React → Spring → FastAPI |
| `python scripts/verify-frozen-scraper.py` | PASS: all 105 source hashes unchanged |

Stale `frontend/test-results` contents were removed. Cleanup and the E2E runner
needed execution outside the sandbox because of access-denied/EPERM errors.
Maven also needed execution outside the sandbox for dependency access.
The first E2E run had one mobile timeout on the existing demo loading screen;
the full second run passed all 16 tests without changing the UI or E2E tests.

Verification fixes were limited to the local CORS fallback origins, correcting
the backend CORS test's request origin from 3000 to its asserted 5173, and making
the smoke script print the actual service URLs rather than hardcoding 5173.
Working application architecture and frozen scraper source were preserved.

Local browser evidence is under `data/verification/phase1-browser.json`,
`phase1-home.png`, and `phase1-connections.png`; these are ignored runtime artifacts.
