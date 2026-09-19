from payment_scraper.core.enums import ProviderId
from payment_scraper.providers.base import ProviderConfig

CONFIG = ProviderConfig(
    provider=ProviderId.GYFTR,
    sources={"SWIGGY": ("https://www.gyftr.com/swiggy-gv",)},
    fixture_sources={"SWIGGY": ("https://www.gyftr.com/swiggy-money",)},
    allowed_domains=frozenset({"www.gyftr.com", "gyftr.com"}),
    terms_url="https://www.gyftr.com/terms-and-conditions",
    browser_fallback=True,
    browser_selector="h1",
)

# Semantic adapter format covered by synthetic fixtures; live DOM is not yet certified.
VOUCHER_SELECTOR = '[data-voucher-id], [itemtype="https://schema.org/Offer"]'
