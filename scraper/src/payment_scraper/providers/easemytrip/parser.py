import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from payment_scraper.core.enums import DiscountType, OfferType, StackingPolicy, TransactionMode
from payment_scraper.core.raw import ParseContext, RawOffer
from payment_scraper.providers.easemytrip.config import OFFER_SELECTOR


def parse(html: str, context: ParseContext) -> list[RawOffer]:
    """Semantic fixtures and the observed public offer detail template."""
    soup = BeautifulSoup(html, "lxml")
    records = []
    for node in soup.select(OFFER_SELECTOR):

        def text(field):
            item = node.select_one(f'[data-emt-field="{field}"]')
            return item.get_text(" ", strip=True) if item is not None else None

        def values(field):
            return [item.get_text(" ", strip=True) for item in node.select(f'[data-emt-field="{field}"]')]

        action = node.select_one("a.offer-link")
        mode = node.get("data-payment-mode", "UNKNOWN")
        records.append(
            RawOffer(
                title=text("title") or "",
                source_id=node.get("data-emt-offer"),
                offer_type=OfferType.PAYMENT_METHOD_DISCOUNT,
                transaction_mode=TransactionMode(mode),
                discount_type=DiscountType(node.get("data-discount-type", "UNKNOWN")),
                discount_text=text("discount"),
                maximum_discount_text=text("cap"),
                minimum_transaction_texts=values("minimum"),
                issuers=values("issuer"),
                instruments=values("instrument"),
                promo_code=text("coupon"),
                valid_from_text=text("start"),
                valid_until_text=text("end"),
                usage_limit=text("usage"),
                terms=values("term"),
                stacking_policy=StackingPolicy.NOT_ALLOWED
                if node.get("data-clubbing") == "no"
                else StackingPolicy.UNKNOWN,
                action_url=urljoin(context.source_url, action["href"])
                if action and action.get("href")
                else None,
                action_label=action.get_text(" ", strip=True) if action else None,
            )
        )
    return records or _parse_public(soup, context)


def has_offer_data(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    return bool(soup.select_one(OFFER_SELECTOR) or (
        soup.find(string=lambda text: text and text.strip() == "What You Get?")
        and soup.find(string=lambda text: text and text.strip() == "Promo Code")
    ))


def _parse_public(soup, context):
    label = soup.find(string=lambda text: text and text.strip() == "What You Get?")
    if not label:
        return []
    # Find the smallest section containing the benefit list AND the coupon/period labels.
    container = next((node for node in label.parents
                      if node.find(string=lambda text: text and text.strip() == "Promo Code")), None)
    if not container:
        return []
    terms = [li.get_text(" ", strip=True) for li in container.select("li")]
    text = " ".join(terms)
    heading = next((h.get_text(" ", strip=True) for h in container.select("h1,h2,h3,h4")
                    if "discount" in h.get_text().lower()), None)
    def labelled(name):
        item = container.find(string=lambda text: text and text.strip() == name)
        sibling = item.parent.find_next_sibling("p") if item else None
        return sibling.get_text(" ", strip=True) if sibling else None
    period = labelled("Booking Period") or ""
    date = re.search(r"(\d{1,2})(?:st|nd|rd|th)? ([A-Za-z]+),? (\d{4})", period)
    coupon = labelled("Promo Code")
    # Only accept an exact formula; an unqualified 'up to' headline is insufficient.
    formula = re.search(r"Max discount will be Rs\.\s*([\d,]+) or (\d+(?:\.\d+)?%) whichever is lower",
                        text, re.I)
    if not heading or not coupon or not formula:
        return []
    minimum = re.search(r"minimum booking value[^.]*?Rs\.\s*([\d,]+)", text, re.I)
    return [RawOffer(
        title=heading, source_id=urlsplit(context.source_url).path, offer_type=OfferType.COUPON,
        discount_type=DiscountType.PERCENTAGE, discount_text=formula[2],
        maximum_discount_text=formula[1],
        minimum_transaction_texts=[minimum[1]] if minimum else [], promo_code=coupon,
        valid_until_text=f"{date[1]} {date[2]} {date[3]}" if date else None,
        stacking_policy=StackingPolicy.NOT_ALLOWED if "cannot be clubbed" in text.lower()
        else StackingPolicy.UNKNOWN,
        terms=terms, action_url=context.source_url, action_label="View offer",
    )]
