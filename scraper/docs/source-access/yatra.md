# YATRA access review

> Historical 2026-09-18 audit. Activation and robots gating described below are superseded.
> This provider is LIVE VERIFIED as of 2026-09-19; see [current verification](../verification.md).

Reviewed: 2026-09-18. Scope: small, attributed, noncommercial hackathon demonstration.

- Public source: https://www.yatra.com/offer/details/icici-bank-no-cost-emi-offers
  and https://www.yatra.com/offer/details/rbl-credit-card-offers . These are the
  entire curated source set; no crawling/discovery runs in production.
- Authentication: no credentials or sessions used; public offer URL.
- Terms: https://www.yatra.com/online/terms-of-service.html and its linked master
  agreement https://www.yatra.com/online/yatra-user-agreement.html . Both readable
  through the web review tool on this date; direct HTTP terms request timed out.
- Evidence: agreement sections 4 and 4.2 limit use to personal/noncommercial use,
  permit limited copying with Yatra attribution, and prohibit wholesale copying.
  This narrow demonstration is assessed against that limited-copy provision.
  It is not permission for commercial deployment or a sitewide crawler.
- Robots: https://www.yatra.com/robots.txt fetched with the production HttpFetcher,
  HTTP 200, SHA-256 `955fa50169abb34506562b06d03fa09b7d1f351a58d876b2f197462fad591e0b`.
  Wildcard rules allow the selected `/offer/details/` path. Runtime checks remain
  mandatory. Narrow disallows override the broad `Allow: /`.
- Allowed hosts: `www.yatra.com`, `yatra.com`; HTTPS port 443 only, public DNS only.
- Rate limit: minimum 3 seconds per host in one service process, including retries
  and robots; respect any longer applicable robots delay.
- Browser: not enabled; first prove public static HTTP content.
- Live activation: temporarily selected as `YATRA` for the bounded review tests;
  **disabled again after both sources repeatedly timed out**. No reliable live
  access was established. Browser fallback remains off. No commercial approval.
- Stop conditions: challenge, authentication, robots refusal, unclear new terms,
  or unavailable source. Do not evade restrictions.

Local policy evidence: `data/raw/yatra/access_review/` (not offer data).

## Actual offer-fetch outcome

Both pages timed out with the honest crawler User-Agent and TLS verification on
Windows. The same result occurred inside the Linux Docker container. Robots returned
200 in both environments. No offer HTTP status/body was received, so no offer snapshot
exists and no live parser selectors, captured fixture or real-offer contract example
can honestly be certified. This does not establish why the server timed out.

The container API request `28f434a5-dee9-4540-ad19-179ef053d15d` ran from
18:03:55.952 to 18:06:03.645 UTC with the default bounded retry policy. It returned
HTTP 503, two FETCH_TIMEOUT errors, zero offers, fixture=false, fetchMethod=null.
The explicit live test at 18:07:12 UTC failed with the same errors (one attempt/page).
Logs show robots at 18:03:56.106 and the first offer at 18:03:59.106 UTC: 3 seconds.
