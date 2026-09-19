# Source access and execution policy

Provider activation is controlled by PROVIDER_YATRA_ENABLED, PROVIDER_GYFTR_ENABLED and
PROVIDER_EASEMYTRIP_ENABLED. The default is true. PLAYWRIGHT_ENABLED controls ordinary
Chromium fallback separately.

Robots observations are informational and auditable. Disallow rules, unavailable robots files,
and unsupported patterns do not stop offer-page attempts. TERMS_REVIEWED_PROVIDERS remains an
optional audit field. Neither robots nor this field establishes legal permission.

Only ordinary public HTTP and browser navigation are implemented. No authentication, private
credentialed APIs, CAPTCHA solving, challenge interaction, stealth or rate-limit evasion is used.
A source failure remains a structured failure and other providers continue.

Current configured public sources:
- [Yatra RBL offer](https://www.yatra.com/offer/details/rbl-credit-card-offers)
- [GyFTR Swiggy vouchers](https://www.gyftr.com/swiggy-gv)
- [EaseMyTrip hotel coupon](https://www.easemytrip.com/offers/flash-sale-on-hotel.html)

All three returned real normalized offers on 2026-09-19. See [verification.md](verification.md).
The provider documents under source-access/ preserve the earlier 2026-09-18 audit; their
disabled-provider conclusions have been superseded by the current configuration and evidence.

Use tools/review_source_access.py for optional policy snapshots. It reports observations only
and never changes provider activation.
