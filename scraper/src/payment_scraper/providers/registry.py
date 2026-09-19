from payment_scraper.core.enums import ErrorCode
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.providers.base import BaseProvider


class ProviderRegistry:
    def __init__(self, providers: list[BaseProvider]):
        self._providers = {}
        for provider in providers:
            key = provider.config.provider.value
            if key in self._providers:
                raise ValueError(f"Duplicate provider: {key}")
            self._providers[key] = provider

    def get(self, identifier: str) -> BaseProvider:
        provider = self._providers.get(identifier.strip().upper())
        if provider is None:
            raise ScraperError(ErrorCode.PROVIDER_NOT_SUPPORTED, "Provider is not registered.")
        return provider

    def all(self) -> list[BaseProvider]:
        return list(self._providers.values())


def default_registry() -> ProviderRegistry:
    from payment_scraper.providers.easemytrip.scraper import EaseMyTripProvider
    from payment_scraper.providers.gyftr.scraper import GyftrProvider
    from payment_scraper.providers.yatra.scraper import YatraProvider

    return ProviderRegistry([GyftrProvider(), YatraProvider(), EaseMyTripProvider()])
