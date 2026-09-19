# Live path audit — 2026-09-19

1. Settings.from_env loads independent PROVIDER_YATRA_ENABLED, PROVIDER_GYFTR_ENABLED,
   PROVIDER_EASEMYTRIP_ENABLED and PLAYWRIGHT_ENABLED flags.
2. ProviderRegistry supplies curated public URLs and provider-specific parsers. Fixture URLs
   are configured separately to preserve the original synthetic contract exports.
3. SourceAccess.check_terms retains its public name for compatibility; it checks provider
   activation only. SourceAccess.check gathers informational robots metadata and validates URLs.
4. HttpFetcher uses native Requests networking. BrowserFetcher uses ordinary Chromium networking,
   not HTTP route fulfillment. Neither provides challenge solving or authentication.
5. ScrapingService snapshots before parsing, normalizes, validates URLs/money/dates, deduplicates
   and reports per-source errors. One recoverable HTTP failure can trigger one browser attempt.
6. CLI, POST /api/v1/scrape and GET /api/v1/offers expose the same canonical offer payload.
7. Diagnostics, snapshots, observation history and provider health preserve evidence separately
   from the canonical schema.

All three providers produced live offers on Windows and Docker. See [verification.md](verification.md)
for counts, timestamps, exact commands, contract hashes and limitations. Prior 2026-09-18 source
access documents are historical evidence, not current execution-policy instructions.
