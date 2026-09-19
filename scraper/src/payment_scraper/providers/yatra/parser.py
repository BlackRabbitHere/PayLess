import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from payment_scraper.core.enums import DiscountType, OfferType, StackingPolicy, TransactionMode
from payment_scraper.core.raw import ParseContext, RawOffer
from payment_scraper.providers.yatra.config import OFFER_SELECTOR


def parse(html: str, context: ParseContext) -> list[RawOffer]:
    """Retain semantic fixtures and parse the observed public bank-offer detail template."""
    soup = BeautifulSoup(html, "lxml")
    result = []
    for section in soup.select(OFFER_SELECTOR):
        values: dict[str, list[str]] = {}
        for label in section.select("dt"):
            value = label.find_next_sibling("dd")
            if value is not None:
                values.setdefault(label.get_text(" ", strip=True).casefold(), []).append(
                    value.get_text(" ", strip=True)
                )

        def first(label):
            return next(iter(values.get(label, [])), None)

        heading = section.select_one("h2, h3")
        terms = [item.get_text(" ", strip=True) for item in section.select(".offer-terms li")]
        action = section.select_one('a[data-action="book"]')
        discount = first("discount")
        mode_text = first("transaction mode")
        mode = (
            TransactionMode(mode_text.strip().upper().replace(" ", "_"))
            if mode_text
            else TransactionMode.UNKNOWN
        )
        result.append(
            RawOffer(
                title=heading.get_text(" ", strip=True) if heading else "",
                source_id=section.get("data-yatra-offer-id"),
                offer_type=OfferType.INSTANT_DISCOUNT,
                transaction_mode=mode,
                discount_text=discount,
                discount_type=DiscountType.PERCENTAGE if discount and "%" in discount else DiscountType.FLAT,
                maximum_discount_text=first("maximum discount"),
                minimum_transaction_texts=values.get("minimum booking", []),
                issuers=values.get("issuer", []),
                instruments=values.get("instrument", []),
                promo_code=first("promo code"),
                valid_from_text=first("valid from"),
                valid_until_text=first("valid until"),
                usage_limit=first("usage limit"),
                terms=terms,
                stacking_policy=StackingPolicy.NOT_ALLOWED
                if first("clubbing") == "Not allowed"
                else StackingPolicy.UNKNOWN,
                action_url=urljoin(context.source_url, action["href"])
                if action and action.get("href")
                else None,
                action_label=action.get_text(" ", strip=True) if action else None,
            )
        )
    return result or _parse_public(soup, context)


def has_offer_data(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    return bool(soup.select_one(OFFER_SELECTOR) or (
        soup.find("h1") and soup.find("table") and soup.find(string=re.compile("booking offer:", re.I))
    ))


def _parse_public(soup, context):
    heading = soup.find("h1")
    if not heading:
        return []
    container = heading.find_parent("aside") or heading.parent
    lines = [li.get_text(" ", strip=True) for li in container.select("li") if not li.find("li")]
    text = " ".join(lines)
    coupon = re.search(r"Promo code:\s*([A-Za-z0-9]+)", text)
    applicable = next((line.split(":", 1)[1].strip() for line in lines
                       if line.startswith("Applicable on:")), "")
    issuer = re.sub(r"\s+Credit Cards?.*", "", applicable, flags=re.I)
    dates = re.search(r"from (\d{1,2} [A-Za-z]+) to (\d{1,2} [A-Za-z]+) (\d{4})", text)
    usage = next((line for line in lines if "once per card" in line.lower()), None)
    common = [line for line in lines if not line.startswith(("Flat ", "Minimum transaction", "Promo code"))
              and len(line) <= 1000]
    minima = {}
    for row in container.select("table tr"):
        cells = row.find_all("td")
        if len(cells) == 3:
            minima[cells[0].get_text(" ", strip=True).lower()] = cells[1].get_text(" ", strip=True)
    records = []
    groups = {
        "domestic flight booking offer:": ("Domestic Flights", "domestic flights"),
        "international flight booking offer:": ("International Flights", "international flights"),
        "hotel booking offer:": ("Domestic Hotels", "domestic hotel"),
    }
    for label in container.select("p"):
        group = groups.get(label.get_text(" ", strip=True).lower())
        if not group:
            continue
        listing = label.find_next_sibling("ul")
        if not listing:
            continue
        for item in listing.select("li"):
            if item.find("li"):
                continue
            line = item.get_text(" ", strip=True)
            percent = re.match(r"Flat (\d+(?:\.\d+)?%) off \(up to INR ([\d,]+)\)", line, re.I)
            flat = re.match(r"Flat INR ([\d,]+) off (.+)", line, re.I)
            if not percent and not flat:
                continue
            # Use the category and passenger/trip condition, never the observed amount, as identity.
            condition = flat[2].rstrip(".") if flat else group[0]
            records.append(RawOffer(
                title=f"{heading.get_text(' ', strip=True)} — {group[0]} — {line}",
                source_id=f"{urlsplit(context.source_url).path}:{group[1]}:{condition}",
                offer_type=OfferType.BANK_OFFER, transaction_mode=TransactionMode.CREDIT_CARD,
                discount_type=DiscountType.PERCENTAGE if percent else DiscountType.FLAT,
                discount_text=percent[1] if percent else flat[1],
                maximum_discount_text=percent[2] if percent else None,
                minimum_transaction_texts=[minima[group[1]]] if group[1] in minima else [],
                issuers=[issuer] if issuer else [], instruments=["Credit Card"] if issuer else [],
                promo_code=coupon[1] if coupon else None,
                valid_from_text=f"{dates[1]} {dates[3]}" if dates else None,
                valid_until_text=f"{dates[2]} {dates[3]}" if dates else None,
                usage_limit=usage, terms=[f"Category: {group[0]}. {line}", *common],
                stacking_policy=StackingPolicy.NOT_ALLOWED if "cannot be clubbed" in text.lower()
                or "cannot be exchanged or clubbed" in text.lower() else StackingPolicy.UNKNOWN,
                action_url=context.source_url, action_label="View offer",
            ))
    return records
