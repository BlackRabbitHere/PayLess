# GYFTR access review

> Historical 2026-09-18 audit. Activation and robots gating described below are superseded.
> This provider is LIVE VERIFIED as of 2026-09-19; see [current verification](../verification.md).

Reviewed: 2026-09-18. Live-enabled: **NO**.

- Configured public source: https://www.gyftr.com/swiggy-money . Not fetched.
- Authentication: no authenticated pages, cookies, or sessions used.
- Applicable terms: https://www.gyftr.com/terms-and-conditions . Actual guarded
  HTTP fetch returned 200, text/html, 16,662 bytes, but only 115 visible characters
  after removing scripts/styles/noscript. Applicable terms remain unreadable.
- Robots: https://www.gyftr.com/robots.txt returned HTTP 200. Runtime check permits
  the configured public path; this does not establish terms permission.
- Evidence: `data/raw/gyftr/access_review/`; full hashes in snapshot JSON sidecars.
- Crawler restrictions: unknown applicable terms; terms gate remains closed.
- Rate limit: minimum 3 seconds between same-host requests; actual review logs
  show requests beginning at 18:04:17.453, 18:04:20.455, 18:04:23.454 UTC.
- Allowed domains: `www.gyftr.com`, `gyftr.com`.
- Browser required: unknown; no provider browser rendering attempted or enabled.
- Reason: source access review is incomplete. Expose only as fixture/demo until
  permission and a real source structure are established. No access-control bypass.
