from payment_scraper.core.enums import ProviderId
from payment_scraper.providers.base import ProviderConfig

CONFIG = ProviderConfig(
    provider=ProviderId.YATRA,
    sources={"YATRA": (
        "https://www.yatra.com/offer/details/rbl-credit-card-offers",
    )},
    allowed_domains=frozenset({"www.yatra.com", "yatra.com"}),
    terms_url="https://www.yatra.com/online/terms-of-service.html",
    browser_fallback=True,
    browser_selector="body",
    fixture_sources={"YATRA": ("https://www.yatra.com/offer/details/icici-bank-no-cost-emi-offers",)},
)
OFFER_SELECTOR = "section[data-yatra-offer-id]"
