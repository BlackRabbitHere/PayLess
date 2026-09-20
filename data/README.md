# Shared data

- `fixtures/scraper/`: byte-for-byte copies of the frozen scraper's three v1 response fixtures and accepted exported OpenAPI. Backend tests consume these directly.
- `scraper-freeze-manifest.json`: SHA-256 source snapshot captured before moving `Scrapper/scraper` to `scraper`. Machine-local environment, caches and runtime data are excluded.
- `runtime/`: ignored local scraper output. Application data is now stored in the Compose PostgreSQL named volume.

`scraper-phase5-overrides.json` records LF-normalized hashes for the two authorized correlation changes; the original manifest is preserved.

Fixtures are synthetic, explicitly labelled and never eligible for production ingestion. Run `python scripts/verify-frozen-scraper.py` from the repository root to check the frozen source.
