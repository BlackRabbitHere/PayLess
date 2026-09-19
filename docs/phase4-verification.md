# Phase 4 — React MVC and travel

## Contracts and boundaries

React submits `{ query, wallet }` to `POST /api/optimize/query`.
The response is the Phase 3 OptimizeResponse contract, mirrored in frontend/src/features/optimization/model/contracts.ts:
OptimizationRequest, OptimizeResponse, PaymentRoute, CostBreakdown, RouteStep, WalletInstrument and ProviderWarning.

Travel uses `POST /api/travel/optimize`:

```json
{
  "origin": "Delhi",
  "destination": "Mumbai",
  "departureDate": "2026-10-24",
  "passengers": 1,
  "wallet": [
    { "issuer": "HDFC", "productName": "Millennia", "instrumentType": "CREDIT_CARD", "network": "VISA" }
  ]
}
```

Use a current/future departure date. Responses contain:
- fares: id, merchant, origin/destination/date/passengers, flight, totalAmount, currency, demo, fareSource.
- optimization: the same OptimizeResponse, or null when there are no fares.
- routeFareIds: route id → fare id, including both winners and every alternative.
- warnings: fare provenance and search limitations.

DemoFareProvider supplies one illustrative flight on Yatra (₹5,650/person) and EaseMyTrip (₹5,459/person).
These totals include the demo provider's mandatory fees and scale with passenger count.
No availability or booking is implied. Delhi–Mumbai is supported in both directions.
Other city pairs return an explicit empty response without acquiring offers.
The FareProvider port can be replaced without changing the travel controller or UI.

OptimizationService accepts priced purchase options and acquires offers once per merchant.
Each option runs through the same OfferEligibilityService, RouteGenerator and CostCalculator.
PaymentRouteOptimizer ranks all calculated routes together. Fare ids namespace route ids to avoid cross-provider collisions.
Steps retain the corresponding purchase merchant. Savings compare each route with its own un-discounted fare.
The demo fare total is treated as the eligible purchase amount; a real provider must supply accurate priced purchase/fee semantics before rollout.

## State and experience

The feature controller owns requests, cancellation, response/loading/error state and reset.
The feature provider spans Home, Travel and Results. Zustand holds only persistent wallet metadata.
Recent searches remain in memory; reloading results requires a fresh search.
Wallet changes discard stale quotes, and a slow or cancelled request cannot replace a later result.
Views expose exact backend money, ordered actions, provider terms, fixtures, eligibility and acquisition failures.
Spring validates merchant queries and travel fields. Unknown wallet credential fields are rejected.

## Reproducible verification

```powershell
cd backend
./mvnw.cmd -B -ntp verify
cd ../frontend
npm test
npm run build
npm run test:e2e
cd ..
python scripts/verify-frozen-scraper.py
```

Playwright starts the real Spring jar, Vite and a test-only HTTP replay of committed scraper fixtures.
No optimization responses are mocked in the two checkpoint journeys. Provider popup destinations are intercepted to avoid real purchases.
API-failure and loading/cancellation tests deliberately intercept Spring responses.

Scenario 1: Swiggy ₹500 → voucher route → ₹487.50 Pay Now / Effective Cost → ₹12.50 saving →
Buy Voucher and View Offer Terms open the approved GyFTR URL.

Scenario 2: Delhi → Mumbai → two labeled fare options + both acquired offer batches + selected wallet →
globally ranked travel routes and the correct booking provider action. Two passengers produce ₹11,300 / ₹10,918 fares.
The committed offers contain EMI/usage restrictions and are correctly excluded; direct EaseMyTrip wins.
Separate Spring tests supply an eligible synthetic HDFC offer and prove wallet-dependent savings through the shared engine.

Also covered: partial/total provider failure with direct fallback, recovery, invalid input, empty fare search,
API failure, real loading, cancellation, wallet persistence, nonpersistent responses, comparison and responsive layouts.

The local machine has no Python 3.12 scraper environment, so this Phase 4 browser verification uses wire-fixture replay,
not the frozen FastAPI runtime or live providers. Normal product startup continues to use the real scraper.
