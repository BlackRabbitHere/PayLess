import hashlib
import json

from payment_scraper.core.enums import VerificationStatus
from payment_scraper.core.models import ScrapedOffer, ScrapeWarning


def fingerprint(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def external_key(offer: ScrapedOffer, source_id: str | None) -> str:
    data = offer.model_dump(mode="json", by_alias=True)
    identity = {
        k: data[k]
        for k in (
            "provider",
            "merchant",
            "offerType",
            "promoCode",
            "eligibleIssuers",
            "eligibleInstrumentTypes",
            "transactionMode",
        )
    }
    identity["sourceIdentity"] = source_id or {"sourceUrl": data["sourceUrl"], "title": data["title"]}
    identity["faceValue"] = data["voucher"]["faceValue"] if data["voucher"] else None
    return f"{offer.provider}-{offer.merchant}-{fingerprint(identity)[:24]}"


def content_hash(offer: ScrapedOffer) -> str:
    data = offer.model_dump(
        mode="json",
        by_alias=True,
        exclude={
            "external_key",
            "content_hash",
            "scraped_at",
            "last_verified_at",
            "verification_status",
        },
    )
    data["terms"] = sorted(data["terms"])
    return fingerprint(data)


def identify(offer: ScrapedOffer, source_id: str | None) -> ScrapedOffer:
    return offer.model_copy(
        update={"external_key": external_key(offer, source_id), "content_hash": content_hash(offer)}
    )


def deduplicate(offers: list[ScrapedOffer]) -> tuple[list[ScrapedOffer], list[ScrapeWarning]]:
    result: dict[str, ScrapedOffer] = {}
    warnings = []
    for offer in offers:
        previous = result.get(offer.external_key)
        if previous is None:
            result[offer.external_key] = offer
        elif previous.content_hash == offer.content_hash:
            severity = {
                VerificationStatus.VERIFIED: 0,
                VerificationStatus.AMBIGUOUS: 1,
                VerificationStatus.INCOMPLETE: 2,
            }
            result[offer.external_key] = max(
                (previous, offer), key=lambda item: severity[item.verification_status]
            )
        elif previous.content_hash != offer.content_hash:
            # Stable representative, with conflict explicitly retained rather than last-write wins.
            complete = [
                item
                for item in (previous, offer)
                if item.verification_status != VerificationStatus.INCOMPLETE
            ]
            chosen = min(complete or (previous, offer), key=lambda item: item.content_hash)
            result[offer.external_key] = chosen.model_copy(
                update={
                    "verification_status": VerificationStatus.AMBIGUOUS
                    if complete
                    else VerificationStatus.INCOMPLETE,
                    "last_verified_at": None,
                }
            )
            warnings.append(
                ScrapeWarning(
                    code="DUPLICATE_CONFLICT",
                    external_key=offer.external_key,
                    message="Same identity has conflicting source terms.",
                )
            )
    return sorted(result.values(), key=lambda item: item.external_key), warnings
