import json
import re
from decimal import Decimal
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from payment_scraper.core.enums import Availability, DiscountType, ErrorCode, OfferType, TransactionMode
from payment_scraper.core.exceptions import ScraperError
from payment_scraper.core.raw import ParseContext, RawOffer
from payment_scraper.providers.gyftr.config import VOUCHER_SELECTOR


def _text(node, selector: str) -> str | None:
    item = node.select_one(selector)
    if item is None:
        return None
    return str(item.get("content") or item.get_text(" ", strip=True)) or None


def _json_products(value):
    if isinstance(value, list):
        for item in value:
            yield from _json_products(item)
    elif isinstance(value, dict):
        kind = value.get("@type", [])
        if kind == "Product" or isinstance(kind, list) and "Product" in kind:
            yield value
        yield from _json_products(value.get("@graph", []))


def parse(html: str, context: ParseContext) -> list[RawOffer]:
    soup = BeautifulSoup(html, "lxml")
    public = _parse_public(soup, context)
    if public:
        return public
    records = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or script.get_text(), parse_float=Decimal)
        except (ValueError, TypeError) as exc:
            raise ScraperError(ErrorCode.PARSER_FAILED, "Provider structured data is malformed.") from exc
        for product in _json_products(data):
            name = str(product.get("name", ""))
            if "swiggy" not in name.lower():
                continue
            offers = product.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]
            properties = product.get("additionalProperty", [])
            if isinstance(properties, dict):
                properties = [properties]
            face = next(
                (
                    str(p.get("value"))
                    for p in properties
                    if isinstance(p, dict)
                    and str(p.get("name", "")).lower() in {"face value", "denomination"}
                    and p.get("value") is not None
                ),
                None,
            )
            for item in offers:
                if not isinstance(item, dict) or item.get("@type") == "AggregateOffer":
                    continue
                currency = item.get("priceCurrency")
                raw = RawOffer(
                    title=name,
                    source_id=str(item.get("sku") or product.get("sku") or "") or None,
                    offer_type=OfferType.VOUCHER_DISCOUNT,
                    transaction_mode=TransactionMode.VOUCHER,
                    face_value_text=face,
                    selling_price_text=str(item["price"]) if item.get("price") is not None else None,
                    action_url=urljoin(context.source_url, str(item.get("url") or context.source_url)),
                    action_label="Buy Voucher",
                    valid_until_text=item.get("priceValidUntil"),
                )
                if currency != "INR":
                    raw.warnings.append("Structured price currency is missing or is not INR.")
                    raw.selling_price_text = None
                availability = str(item.get("availability", ""))
                if availability.endswith("/InStock"):
                    raw.availability = Availability.AVAILABLE
                elif availability.endswith("/OutOfStock"):
                    raw.availability = Availability.UNAVAILABLE
                records.append(raw)
    # Keep semantic observations as well, so discrepancies are not silently overwritten.
    for node in soup.select(VOUCHER_SELECTOR):
        face = _text(node, '[data-field="face-value"], [itemprop="faceValue"]')
        price = _text(node, '[data-field="selling-price"], [itemprop="price"]')
        if face is None and price is None:
            continue
        action = node.select_one('a[data-action="buy"], a[itemprop="url"]')
        discount = _text(node, '[data-field="discount"]')
        records.append(
            RawOffer(
                title=_text(node, '[data-field="title"], [itemprop="name"]') or "Swiggy Money Voucher",
                source_id=node.get("data-voucher-id"),
                offer_type=OfferType.VOUCHER_DISCOUNT,
                transaction_mode=TransactionMode.VOUCHER,
                face_value_text=face,
                selling_price_text=price,
                discount_text=discount,
                discount_type=DiscountType.PERCENTAGE
                if discount and "%" in discount
                else DiscountType.UNKNOWN,
                terms=[item.get_text(" ", strip=True) for item in node.select('[data-field="terms"] li')],
                minimum_transaction_texts=[
                    item.get_text(" ", strip=True)
                    for item in node.select('[data-field="minimum-transaction"]')
                ],
                valid_from_text=_text(node, '[data-field="valid-from"]'),
                valid_until_text=_text(node, '[data-field="valid-until"]'),
                action_url=urljoin(context.source_url, action["href"])
                if action and action.get("href")
                else None,
                action_label=action.get_text(" ", strip=True) if action else None,
                availability={
                    "available": Availability.AVAILABLE,
                    "unavailable": Availability.UNAVAILABLE,
                }.get(node.get("data-availability"), Availability.UNKNOWN),
            )
        )
    return records


def has_offer_data(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    return bool(soup.select_one(VOUCHER_SELECTOR) or (
        soup.select_one("#__NEXT_DATA__") and soup.find(string=re.compile(r"YOU PAY"))
    ) or soup.select_one('script[type="application/ld+json"]'))


def _parse_public(soup, context):
    """Observed retail template: exact displayed prices plus embedded product IDs/payment terms."""
    script = soup.select_one("#__NEXT_DATA__")
    if not script:
        return []
    try:
        state = json.loads(script.string or script.get_text(), parse_float=Decimal)
        brand = state["props"]["pageProps"]["reduxState"]["brandInfo"]
    except (ValueError, KeyError, TypeError):
        return []
    details = brand.get("brandDetailStore", {})
    if "swiggy" not in details.get("brand_name", "").lower():
        return []
    products = {str(p["mrp"]): p for p in brand.get("productDetailStore", []) if "mrp" in p}
    instructions = BeautifulSoup(details.get("important_instruction", ""), "lxml")
    terms = [li.get_text(" ", strip=True) for li in instructions.select("li")]
    records = []
    for label in soup.find_all(string=re.compile(r"^YOU PAY")):
        row = label.parent.parent.parent
        value = row.get_text(" ", strip=True)
        match = re.fullmatch(
            r"₹\s*([\d,.]+) DISCOUNT \(\s*([\d.]+)\s*%\) [\d.]+ "
            r"SAVING\(₹\)\s*([\d.]+) YOU PAY\(₹\)\s*([\d.]+) ADD", value,
        )
        if not match:
            continue
        face, percent, saving, price = match.groups()
        product = products.get(face.replace(",", ""), {})
        if not product:
            continue
        gateways = [p for p in brand.get("brandPgListStore", [])
                    if Decimal(str(p.get("pg_discount", 0))) == Decimal(percent)]
        methods = [p["pg_name"] for p in gateways]
        warnings = []
        if Decimal(face.replace(",", "")) - Decimal(price) != Decimal(saving):
            warnings.append(f"Displayed saving {saving} conflicts with face {face} minus price {price}.")
        if not methods:
            warnings.append("Payment method for displayed discount could not be confirmed.")
        records.append(RawOffer(
            title=f"{details['brand_name']} — INR {face}",
            source_id=str(product["product_id"]), offer_type=OfferType.VOUCHER_DISCOUNT,
            transaction_mode=TransactionMode.VOUCHER, face_value_text=face, selling_price_text=price,
            discount_text=percent + "%", discount_type=DiscountType.PERCENTAGE,
            instruments=["WALLET" if name == "e-Pay" else name for name in methods],
            terms=[*terms, f"Displayed discount applies to: {', '.join(methods)}.",
                   f"Displayed saving INR {saving}; payment-method discounts may differ."],
            action_url=context.source_url, action_label="Buy Voucher", warnings=warnings,
        ))
    return records
