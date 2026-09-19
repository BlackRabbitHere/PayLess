# Application architecture through Phase 3

The workspace root is the payment-optimizer monorepo (its local directory name may differ).
The frozen scraper was relocated from `Scrapper/scraper` to `scraper` without source or contract edits.
`Scrapper/` now contains only ignored machine-local Python tools, caches and the existing virtual environment.

## Spring MVC

Each feature owns its application, domain, DTO, controller and/or persistence packages as requested.
Empty future packages have tracked `package-info.java` files. No JPA, JDBC, database driver, migrations or PostgreSQL service is present.

Controller -> application service -> domain port -> external adapter.
The `OfferSource` port returns application-owned `OfferBatch`/`Offer` types.
Only `integration.scraper` knows wire DTOs, HTTP paths, schema versions and mapping details.
Controllers delegate and validate requests. They contain no scraping, ranking, calculations or query parsing.
ArchUnit enforces domain independence, adapter isolation and the controller boundary.

The Phase 1 offer endpoint remains a development contract probe:
`POST /api/v1/optimization/scraper-check`. It is absent in production.
It exercises all three frozen provider contracts without ingestion, ranking or persistence.
The mapper preserves decimal strings as BigDecimal, nullable values, timestamps, UNKNOWN states, warnings and partial-result errors.
Its application preview serializes amounts as strings. It does not interpret VERIFIED as purchase eligibility.

`GET /api/v1/system/status` calls the scraper health endpoint through a port.
`GET /actuator/health` checks the backend process independently of the scraper.
Upstream unavailability returns 503, malformed responses/other upstream failures return 502,
and invalid application requests return 400 using ProblemDetail. No automatic retries or fallback fixture responses are added.
Fixture use is explicit and rejected under the production profile.

## React

The existing Routewise demo UI is retained by request.
`app/router` composes routes, `app/providers` owns shared demo context, and `app/config` reads environment settings.
`features/optimization` owns the search/results views, controller hooks, model, state and backend probe API.
`features/wallet` owns wallet views, controllers and model operations.
`features/travel/model` retains flight fixtures. Query understanding and redirect safety have their own feature models.
`shared/api/httpClient.ts` is the only fetch transport; components never call fetch or Axios directly.

Existing financial calculations, ranking and parsing remain explicitly demo model code.
No new production optimization behavior was implemented. Demo searches continue to use local fixtures,
and demo wallet/history remain in browser localStorage. Backend observations are not mixed into demo rankings.
The separate `/system` screen checks the API path and reports fixture/live mode honestly.

Frontend boundary tests guard direct HTTP calls in views and prevent views from importing the calculation/parser implementations.
Existing unit and browser tests protect the retained demo behavior.

## References

- [Spring RestClient guidance](https://docs.spring.io/spring-boot/3.5/reference/io/rest-client.html)
- [Vite environments and modes](https://vite.dev/guide/env-and-mode)
- Frozen scraper contract: `scraper/docs/api-contract.md` and `scraper/docs/spring-boot-integration.md`.

The default read timeout is 30 seconds. Live scraper operations use the frozen scraper's recommended 180-second background budget;
override SCRAPER_READ_TIMEOUT explicitly for the acquisition checkpoint. The React demo never triggers live scraping.
The Phase 3 backend optimization endpoint requests acquisition without force refresh; the scraper may fetch on a cache miss.

## Phase 2 boundary

`TextNormalizer -> AmountExtractor -> MerchantMatcher -> CategoryResolver -> PurchaseContext` runs entirely inside Spring.
Amounts use BigDecimal with exactly two decimal places; ambiguous, missing, nonpositive and fractional-paise values are rejected.
Unicode normalization, INR/Rs/₹ markers, Indian/international digit grouping and compact currency markers are supported.
Merchant matching uses token-bounded exact names, explicit aliases, then bounded Levenshtein distance.
Confidence is a deterministic match-quality score (exact 1.00, alias 0.96, fuzzy 0.85), not a calibrated probability.
The frozen merchant catalog is intentionally small: SWIGGY/FOOD_DELIVERY, YATRA/TRAVEL, EASEMYTRIP/TRAVEL.

Business callers use `OfferAcquisitionService.acquire(PurchaseContext[, forceRefresh]) -> List<Offer>`.
The service selects GYFTR only for SWIGGY, YATRA only for YATRA, and EASEMYTRIP only for EASEMYTRIP.
It calls the domain `OfferSource` port, implemented by `ScraperAdapter`, which invokes `ScraperClient` and `ScraperOfferMapper`.
The client only serializes requests, performs bounded HTTP and deserializes responses/errors. It has no query or financial logic.
The five integration DTOs are `ScraperRequest`, `ScraperResponse`, `ScrapedOfferDto`, `ScraperProviderStatusDto`, and `ScraperErrorDto`.
All wire DTOs remain confined to integration. HTTP error diagnostics retain string codes and retryability inside the adapter;
the public API emits controlled ProblemDetail messages without raw upstream diagnostics. There are no retries or fixture fallbacks.

`ScraperOfferMapper` checks v1, envelope/offer identity, required fields, money, dates and source URLs, then produces immutable domain offers.
Nulls, UNKNOWN, terms, payment-method restrictions, content hashes, warnings and partial-provider errors survive mapping.
Acquisition includes only VERIFIED offers; AMBIGUOUS and INCOMPLETE observations stay out of the acquired offer list.
An all-unverified PARTIAL batch therefore has no acquired offers and retains its diagnostics; it is not presented as a successful eligible purchase.
Production always rejects fixtures. VERIFIED does not establish eligibility, validity for a specific purchase, or savings.

`POST /api/v1/offers/acquisition-check` is an explicit development checkpoint, absent in production.
It accepts `{sentence, forceRefresh}` and returns `{context, acquisition}` with domain offers and acquisition diagnostics.
It performs synchronous acquisition to prove the requested boundary. The React demo is not connected to it;
production refresh scheduling, caching policy, eligibility, route generation and optimization remain future work.
See [Phase 2 verification](phase2-verification.md) for the genuine GyFTR checkpoint and reproduction commands.

## Phase 3 application flow

`OptimizationController -> OptimizationService -> QueryUnderstandingService -> PurchaseContext -> OfferAcquisitionService`
`-> OfferEligibilityService -> RouteGenerator -> CostCalculator -> PaymentRouteOptimizer -> RouteStepBuilder`
`-> RedirectSafetyValidator -> OptimizeResponse`.

The new endpoint is `POST /api/optimize/query`. The controller only validates, delegates and returns an HTTP response.
Wallet values are metadata only, scoped to the request. Unknown input properties are rejected at this boundary even though
the frozen scraper adapter tolerates unknown wire properties. Business time is provided by an injectable UTC Clock.
Offer acquisition isolates failures per configured provider, preserves partial diagnostics, and does not force refresh.
Only calculated routes enter the optimizer. BigDecimal monetary arithmetic belongs exclusively to CostCalculator;
ArchUnit guards controller dependencies and monetary arithmetic placement.
Redirect actions are generated from a closed backend catalog and validated against exact approved HTTPS destinations.
Source metadata retains verification timestamps, hashes, terms and fixture markers independently of purchase eligibility.
React remains unchanged. See [Phase 3 verification and rules](phase3-verification.md) for the supported scope and curl checkpoint.
