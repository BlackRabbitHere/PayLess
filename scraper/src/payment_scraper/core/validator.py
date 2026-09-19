from decimal import Decimal

from payment_scraper.core.enums import DiscountType, OfferType, VerificationStatus
from payment_scraper.core.models import ScrapedOffer


def verify_offer(offer: ScrapedOffer, conflicts: list[str]) -> tuple[ScrapedOffer, list[str]]:
    warnings = list(conflicts)
    if offer.valid_until and offer.valid_until < offer.scraped_at:
        warnings.append("Offer validity ended before this observation.")
    if offer.valid_from and offer.valid_from > offer.scraped_at:
        warnings.append("Offer validity has not started at this observation.")
    incomplete = False
    voucher = offer.voucher
    if offer.offer_type == OfferType.VOUCHER_DISCOUNT:
        incomplete = not voucher or voucher.face_value is None or voucher.selling_price is None
        if not incomplete:
            if voucher.face_value == 0 or voucher.selling_price > voucher.face_value:
                warnings.append("Voucher price/value relationship is inconsistent.")
            elif offer.discount.type == DiscountType.PERCENTAGE and offer.discount.value is not None:
                saving_percent = (voucher.face_value - voucher.selling_price) * 100 / voucher.face_value
                if abs(saving_percent - offer.discount.value) > Decimal("0.05"):
                    warnings.append(
                        f"Displayed percentage {offer.discount.value}% conflicts with calculated "
                        f"{saving_percent}% (faceValue={voucher.face_value}, "
                        f"sellingPrice={voucher.selling_price})."
                    )
    else:
        incomplete = (
            offer.discount.value is None
            or offer.discount.type == DiscountType.UNKNOWN
            or offer.offer_type == OfferType.UNKNOWN
        )
    status = (
        VerificationStatus.INCOMPLETE
        if incomplete
        else VerificationStatus.AMBIGUOUS
        if warnings
        else VerificationStatus.VERIFIED
    )
    if incomplete:
        warnings.append("Important offer values are missing.")
    return offer.model_copy(
        update={
            "verification_status": status,
            "last_verified_at": offer.scraped_at if status == VerificationStatus.VERIFIED else None,
        }
    ), warnings
