from payment_scraper.core.enums import ProviderId
from payment_scraper.providers.base import ProviderConfig

CONFIG = ProviderConfig(
    provider=ProviderId.EASEMYTRIP,
    sources={"EASEMYTRIP": ("https://www.easemytrip.com/offers/flash-sale-on-hotel.html",)},
    fixture_sources={"EASEMYTRIP": ("https://www.easemytrip.com/offers/bank-deals.html",)},
    allowed_domains=frozenset({"www.easemytrip.com", "easemytrip.com"}),
    terms_url="https://www.easemytrip.com/terms.html",
    browser_fallback=True,
    browser_selector="body",
)
OFFER_SELECTOR = "article[data-emt-offer]"
