# Phase 3: optimization HTTP checkpoint

`POST /api/optimize/query` is the application endpoint, available in all Spring profiles.
It accepts `query` (`sentence` is also accepted) and an optional metadata-only `wallet` array.
Omitting the wallet returns a direct UPI candidate and any applicable unrestricted UPI/voucher offers.
Wallet instruments contain exactly `issuer`, `productName`, `instrumentType`, and `network`.
Supported instruments: `UPI`, `CREDIT_CARD`, `DEBIT_CARD`. Networks: `NONE`, `UNKNOWN`, `VISA`, `MASTERCARD`, `RUPAY`, `AMEX`, `DINERS`.
Unknown request/wallet properties, including cardNumber, CVV, PIN, OTP, credentials, and redirect URLs, return HTTP 400.
The wallet is request-scoped metadata; there is no credential storage or wallet persistence.

## Reproduce with curl or Postman

Start Spring and the scraper as described in the root README. From the repository root:

```powershell
curl.exe --fail-with-body --silent --show-error -H "Content-Type: application/json" --data-binary "@docs/phase3-request.json" http://localhost:8080/api/optimize/query
```

On Unix use `curl` instead of `curl.exe`. In Postman use POST, the same URL, JSON body, and the contents of `phase3-request.json`.

The response contains `context`, `currency`, `bestEffectiveCostRoute`, `bestPayNowRoute`, `alternatives`,
per-instrument `eligibility` results, acquisition `sources`, and `warnings`.
Each route contains its payment instrument, full cost breakdown, ordered steps, source metadata, and relevant warnings.
An action URL is either null or an exact backend-owned HTTPS destination. Scraped action URLs are never used as button destinations.
Source URLs are provenance, not approved redirect actions.

With the frozen GyFTR fixture, the INR 500 voucher costs INR 487.50, so both winners cost INR 487.50
and save INR 12.50. The HDFC wallet request produces four candidates (UPI/card direct and UPI/card voucher),
with three alternatives when the winners coincide. All fixture evidence is explicitly labelled synthetic.
During complete acquisition failure, HTTP 200 still returns direct routes costing INR 500.00 and an acquisition-unavailable warning.
Invalid queries and invalid wallet payloads return HTTP 400 before acquisition.

## Automated verification

```powershell
cd backend
./mvnw.cmd -B -ntp verify
```

The deterministic suite uses a local HTTP scraper contract stub and a real Spring HTTP server.
`ScraperIntegrationTest.curlCompletesThePhaseThreeHttpCheckpoint` also executes actual curl against that server,
validates winners, alternatives, steps, source metadata and warnings, and writes its request and response to
`data/verification/phase3/`. Curl must be installed for this checkpoint.
These are contract-fixture checks, not live commercial-offer verification.
The separate Phase 2 live acquisition test remains opt-in through `RUN_LIVE_SCRAPER=true`.

Verified on 2026-09-19: 110 tests discovered, 109 passed, one opt-in live test skipped, zero failures/errors.
The actual curl checkpoint returned INR 487.50 for both winners, three alternatives and four voucher steps.
All 105 frozen scraper files passed the original SHA-256 manifest check, and `git diff --check` passed.
The default JAR was held open by an existing process on Windows. Full Maven `verify`, including executable JAR packaging,
succeeded with a temporary POM that changed only the build directory to `backend/target/phase3-verification`.
That temporary POM was removed; the existing process was not stopped. Restart the backend to load the new endpoint.

Unit coverage includes each eligibility restriction, exact validity/minimum boundaries, unconfirmed usage,
explicit stacking permission, all supported candidate subsets, HALF_UP rounding, caps, voucher remainder,
no duplicate voucher discount, deferred cashback, deterministic ranking/ties, safe redirects and provider failure isolation.
HTTP tests cover invalid wallet/query input, forbidden fields, malicious scraped action URLs, partial acquisition and total outages.

## Deliberate business boundaries

- The provider catalog retains actual merchant support: SWIGGY -> GYFTR, YATRA -> YATRA, EASEMYTRIP -> EASEMYTRIP.
  Failure isolation iterates all providers configured for a merchant; unrelated merchants are never queried as substitutes.
- VERIFIED describes source verification, not purchase eligibility. Known issuer, type, network, mode, minimum, validity,
  usage and stacking restrictions are independently evaluated. All rejection codes are retained.
- The frozen scraper has no structured network field. Domain offers support network restrictions, but the adapter supplies
  no declared network restrictions and the response warns the user to check source terms.
- Free-text limited-use rules cannot be proven from a metadata-only wallet and are excluded with `USAGE_RULE_UNCONFIRMED`.
  Missing validity bounds and absent usage rules are not invented; published terms and explicit warnings accompany such offers.
  Unknown availability, unpriced benefits, EMI/interest-bearing routes, oversized vouchers and unsupported voucher destinations are excluded.
- One voucher of its published denomination is used per voucher route. Any remaining purchase amount is paid directly.
  Selling price is authoritative; the advertised percentage is not deducted a second time.
  Voucher/payment or voucher/redemption offer stacking is not inferred because the source does not encode those scopes.
- Direct offer combinations require every member to declare `ALLOWED`. Each benefit is computed on the original eligible
  purchase amount, capped individually, with total immediate discount bounded by the purchase and deferred rewards bounded by pay-now.
  No unpriced charges, points conversion, eligibility inferred from product names, or invented card rewards are added.
- All money arithmetic belongs to `CostCalculator`, using BigDecimal and two-decimal HALF_UP rounding.
  `payNow = originalAmount - immediateDiscount`; `effectiveCost = payNow - deferredReward`; `saving = originalAmount - effectiveCost`.
- Effective ranking is cost, pay-now, confidence, complexity, then a stable route ID. Pay-now ranking prioritizes payment
  and uses the same ordering for ties. Alternatives exclude both winners without duplicating a shared winner.
  Confidence is a deterministic verification score, not a statistical probability; direct routes have no offer dependency.
- Redirect validation accepts only exact backend-owned destinations bound to providers. HTTPS alone does not qualify a URL.
  User-supplied destinations, credentials, ports, query strings, fragments and lookalike hosts are rejected.
- React remains on its existing demo integration. No frontend changes are part of this phase.
