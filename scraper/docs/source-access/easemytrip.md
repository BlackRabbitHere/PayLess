# EASEMYTRIP access review

> Historical 2026-09-18 audit. Activation and robots gating described below are superseded.
> This provider is LIVE VERIFIED as of 2026-09-19; see [current verification](../verification.md).

Reviewed: 2026-09-18. Live-enabled: **NO**.

- Public source registry: https://www.easemytrip.com/offers/bank-deals.html .
  Offer content was not fetched during this review.
- Authentication: no authenticated access attempted; only public policy documents.
- Applicable terms: https://www.easemytrip.com/terms.html , read through the web
  review tool and subsequently the guarded HttpFetcher (HTTP 200, 33,081 bytes,
  22,588 visible text characters). The Copyright & Trademark and Transmitted Material sections restrict
  copying without permission except as needed to use the site's paid services.
  No permission for this collection project was supplied. Leave live access disabled.
- Robots: https://www.easemytrip.com/robots.txt returned HTTP 200 through the actual
  HttpFetcher. SHA-256 is recorded in `data/raw/easemytrip/access_review/`.
  The 22-byte file contains `User-Agent: *` and `Allow: *`. The initial conservative
  check refused the wildcard; explicit support for this universal pattern was then
  added and tested. More complex unsupported patterns still fail closed.
  Robots permission does not establish terms permission.
  The completed runtime check returned allowed for the configured bank-deals URL;
  `offerFetched` remained false.
- Allowed domains: `www.easemytrip.com`, `easemytrip.com`.
- Rate limit decision: minimum 3 seconds, or a longer applicable robots delay, for
  any future approved run. No offer requests were sent.
- Browser automation: not enabled, not used to change the access outcome.
- Reason: copying permission not established. The adapter remains a synthetic fixture/demo.
