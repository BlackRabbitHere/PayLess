from payment_scraper.core.raw import ParseContext, RawOffer
from payment_scraper.providers.base import BaseProvider
from payment_scraper.providers.easemytrip import parser
from payment_scraper.providers.easemytrip.config import CONFIG


class EaseMyTripProvider(BaseProvider):
    config = CONFIG

    def parse(self, html: str, context: ParseContext) -> list[RawOffer]:
        return parser.parse(html, context)

    def has_offer_data(self, html: str) -> bool:
        return parser.has_offer_data(html)
