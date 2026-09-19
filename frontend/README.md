# Routewise — Payment Optimizer frontend

A React + TypeScript + Tailwind CSS demo retained inside the Phase 1 monorepo. Built with Vite, React Router and Lucide icons. Search and wallet behavior remain illustrative; the separate `/system` page calls Spring Boot and checks its FastAPI connection. No authentication, payment processing or real card details.

## Run

Requires Node.js 20.19+ or 22.12+.

```sh
npm install
npm run dev
```

Open http://localhost:5173. Production build: `npm run build`. Serve the built frontend with `npm run preview`. A static host must fall back to `index.html` for the React Router paths. See the root README for environment profiles, API settings and three-service startup.

## 90-second demo

1. Open **My Wallet**. Three demo products are selected. Toggle products or use **Add Payment Product**; no credentials are requested.
2. Return **Home**, choose **Book a Flight / Load Flight Demo**, then **Find Best Payment Route**.
3. Show Yatra + ICICI: **₹4,988 Pay Now**, **₹4,908 Effective Cost**. The ₹80 reward arrives later; ₹742 total savings uses Yatra’s ₹5,650 no-offer total.
4. Choose **Compare the two** to compare with the lowest listed fare: EaseMyTrip ₹5,260 + ₹199 fees = ₹5,459 without an offer.
5. Expand **Cost breakdown**, **Why this works**, **Offer Conditions**, and **Source & verification**. Switch sorting to **Lowest Pay Now** or **Highest Rewards**.
6. Open **View Route**, see the ordered steps and sample promo code, then **Open Yatra**. This opens the provider homepage in a new tab; it does not pre-fill a booking.
7. Return Home and type **I am ordering food on swigy and it costs 500 rs**. Select **Review purchase**, confirm **Swiggy / ₹500 / Food Delivery**, then **Find Best Payment Route**. The ₹500 voucher costs **₹487.50**, saving **₹12.50** immediately.
8. Open **View Route** → **Buy Voucher** (GyFTR catalogue), then **Open Swiggy**. Follow the redemption instructions in the Swiggy app. The amount is fictional demo data; the real provider may have different prices, voucher denominations, or availability.

Enable SBI Cashback in My Wallet to demonstrate that Swiggy’s lowest Effective Cost can be a different route from its lowest Pay Now.

## Purchase understanding and destinations

- Natural-language parsing is local TypeScript: normalization, Indian currency parsing, merchant aliases, constrained edit-distance matching, category inference and missing fields. No model, remote service, or API is called.
- Swiggy, Zomato, Myntra, ixigo, Yatra, EaseMyTrip, Cleartrip and MakeMyTrip are recognized. Unknown merchants, multiple merchants, conflicting amounts, invalid number grouping, and extra decimal places require correction. Missing amounts are never copied from a previous search.
- Confirm the interpretation or use **Edit**. Query confidence is internal interpretation metadata and is never used in financial calculations. The travel form retains From, To, Departure and Travellers.
- Offers match both purchase mode and merchant. The existing everyday offer dataset covers Swiggy; other recognized merchants show an honest direct-payment fallback with zero assumed savings.
- `PaymentRoute.steps` contains ordered `RouteStep` objects. The results card exposes the first action; Route Details exposes all actions. Comparison counts the actual steps.
- `sourceUrl` is a provider reference; `actionUrl` is where the step is performed. Demo offer rules remain the financial source of truth. External reference pages do not verify the fictional discount. `status` remains the existing verification-status field; `lastVerifiedAt` is explicitly a demo timestamp.
- Destinations require HTTPS and an exact approved provider host (root or `www` only). Unknown domains, look-alikes, credentials and nonstandard ports are rejected. All external links use `target="_blank"` and `rel="noopener noreferrer"`.
- Replace the display name and wordmark in `src/app/config/brand.ts`. The localStorage namespace stays stable to preserve existing saved demos.

## Interactions and fallback states

- Results **Demo controls**: standard, no eligible offer, stale source, ambiguous sources, and empty wallet.
- Clear wallet selection to compare merchant prices without personalized offers. **Restore demo wallet** recovers the starting selection.
- Compare two or three routes, expand calculations and source information, inspect excluded offers, and sort alternatives.
- Changes to date, passenger count, and order amount recalculate eligibility and costs. City pairs share the same clearly labelled illustrative fare fixtures; this is not a flight search service. Fees and discount caps apply per booking; base fares scale with adult count.
- Voucher eligibility is limited to ₹100–₹1,000. Deferred cashback is capped at ₹500 in applicable demo offers. Demo validity is September–December 2026.
- Profile menu → **Reset all demo data** restores the initial wallet and clears recent searches.
- Demo wallet, last purchase, and up to six recent searches persist only in browser localStorage. Storage failures fall back to memory.
- Dialogs support keyboard navigation, Escape dismissal, and focus restoration. Animations respect reduced-motion preferences.

## Calculation model

```
Instant Discount = min(rate × eligible base amount, maximum discount)
Pay Now = base amount + convenience fee − Instant Discount
Effective Cost = Pay Now − Estimated Rewards
Savings = base amount + convenience fee − Effective Cost
```

Fictional flight instant discounts round down to a whole rupee; voucher discounts round to the nearest paise. Fees are excluded from the eligible discount amount. Monetary reward assumptions are shown beside each route. Unselected products, failed eligibility, stale sources, and ambiguous terms cannot win recommendations. All source dates and offers are explicitly demo information; no live verification is claimed.

## Project structure

```
src/
  app/            Router, providers, branding and environment configuration
  features/
    optimization/ model, controller hooks, API client, search/results views
    wallet/       Wallet model, controller hooks and views
    travel/       Flight demo model and fixtures
    query/        Deterministic understanding model and editing controller
    redirect/     Destination safety model
  shared/         Components, API transport, types and shared utility extension points
  styles.css      Tailwind import, visual theme and responsive layouts
tests/
  optimizer.test.ts        Financial calculations and eligibility tests
  queryUnderstanding.test.ts  Amount formats, aliases, ambiguity and missing information
  redirectSafety.test.ts   URL rejection, provenance and route step contracts
  e2e/prototype.spec.ts    Desktop and mobile user journeys
```

## Validation

```sh
npm test
npm run build
npm run test:e2e
```

The browser tests use an installed Google Chrome (`channel: 'chrome'`) and automatically launch Vite on port 4173 when needed. They cover both desktop and mobile viewport layouts, the two demos, parsing and corrections, safe new-tab actions, wallet changes, comparison, explanations, fallback states, local persistence, reset, validation and browser console errors. Provider navigation is intercepted in tests to verify the destination and opener protection without depending on external websites; tests do not purchase vouchers or book flights. To use Playwright-managed Chromium instead, remove `channel: 'chrome'` from `playwright.config.ts` and run `npx playwright install chromium`.

