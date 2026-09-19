from abc import ABC, abstractmethod
from dataclasses import dataclass

from payment_scraper.core.enums import ProviderId
from payment_scraper.core.raw import ParseContext, RawOffer


@dataclass(frozen=True)
class ProviderConfig:
    provider: ProviderId
    sources: dict[str, tuple[str, ...]]
    allowed_domains: frozenset[str]
    terms_url: str
    browser_fallback: bool = False
    browser_selector: str | None = None
    live_ready: bool = False
    fixture_sources: dict[str, tuple[str, ...]] | None = None


class BaseProvider(ABC):
    config: ProviderConfig

    def supports(self, merchant: str) -> bool:
        return merchant in self.config.sources

    def get_source_urls(self, merchant: str) -> list[str]:
        return list(self.config.sources.get(merchant, ()))

    @abstractmethod
    def parse(self, html: str, context: ParseContext) -> list[RawOffer]:
        """Extract source values; the service normalizes them into ScrapedOffer."""

    @abstractmethod
    def has_offer_data(self, html: str) -> bool:
        """Whether static HTML contains this provider's supported offer structure."""
