All HTML in this directory is synthetic, authored for deterministic adapter tests.
It is not a saved live provider page and must not be presented as current commercial data.
Changing live DOM selectors requires an authorized public snapshot and regression coverage.
# Captured live regression fixtures

`live/` contains sanitized captures of real public provider responses from 2026-09-19.
Each HTML file has a provenance JSON sidecar with capturedFromLive, captureDate,
provider, sourceUrl, raw source SHA-256, sanitized fixture SHA-256 and requestId.
These are offline regression inputs; replaying them is never a live verification.
The original synthetic fixtures and their generated JSON response contracts remain unchanged.
