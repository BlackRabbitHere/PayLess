package com.paymentoptimizer.offers.application;

import com.paymentoptimizer.offers.domain.*;
import com.paymentoptimizer.query.domain.PurchaseContext;
import com.paymentoptimizer.wallet.domain.WalletInstrument;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;
import org.springframework.stereotype.Service;

@Service
public class OfferEligibilityService {
    public EligibilityResult evaluate(Offer offer, PurchaseContext purchase, WalletInstrument instrument,
            String mode, List<Offer> applied, Instant now) {
        var reasons = new ArrayList<String>();
        check(offer.merchant().equals(purchase.merchant().name()), "MERCHANT_MISMATCH", reasons);
        check(matches(offer.eligibleIssuers(), instrument.issuer()), "ISSUER_MISMATCH", reasons);
        check(matches(offer.eligibleInstrumentTypes(), instrument.instrumentType().name())
                || (offer.eligibleInstrumentTypes().contains("CARD") && "CARD".equals(instrument.transactionMode())), "CARD_TYPE_MISMATCH", reasons);
        check(matches(offer.eligibleNetworks(), instrument.network().name()), "NETWORK_MISMATCH", reasons);
        check(offer.transactionMode().equals(mode) || ("CARD".equals(mode)
                && offer.transactionMode().equals(instrument.instrumentType().name())), "TRANSACTION_MODE_MISMATCH", reasons);
        var eligibleAmount = offer.voucher() == null ? purchase.amount() : offer.voucher().sellingPrice();
        check(offer.minimumTransaction() == null || (eligibleAmount != null && eligibleAmount.compareTo(offer.minimumTransaction()) >= 0),
                "MINIMUM_TRANSACTION_NOT_MET", reasons);
        check(offer.validFrom() == null || !now.isBefore(offer.validFrom()), "OFFER_NOT_STARTED", reasons);
        check(offer.validUntil() == null || !now.isAfter(offer.validUntil()), "OFFER_EXPIRED", reasons);
        check(offer.usageLimit() == null || Set.of("UNLIMITED", "NONE").contains(offer.usageLimit()),
                "USAGE_RULE_UNCONFIRMED", reasons);
        check(applied.isEmpty() || ("ALLOWED".equals(offer.stackingPolicy())
                && applied.stream().allMatch(o -> "ALLOWED".equals(o.stackingPolicy()))), "STACKING_NOT_ALLOWED", reasons);
        check(applied.stream().noneMatch(o -> o.externalKey().equals(offer.externalKey())), "DUPLICATE_OFFER", reasons);
        check("VERIFIED".equals(offer.verificationStatus()), "OFFER_NOT_VERIFIED", reasons);
        check("AVAILABLE".equals(offer.availability()), "AVAILABILITY_UNCONFIRMED", reasons);
        check(Set.of("CARD", "UPI", "VOUCHER").contains(mode), "UNSUPPORTED_TRANSACTION_MODE", reasons);
        check(supportedBenefit(offer), "UNSUPPORTED_BENEFIT", reasons);
        if ("VOUCHER".equals(mode)) {
            check("GYFTR".equals(offer.provider()) && "SWIGGY".equals(offer.merchant()), "VOUCHER_PROVIDER_UNSUPPORTED", reasons);
            var v = offer.voucher();
            check(v != null && positive(v.faceValue()) && nonnegative(v.sellingPrice())
                    && v.faceValue().compareTo(purchase.amount()) <= 0
                    && v.sellingPrice().compareTo(v.faceValue()) <= 0, "VOUCHER_DENOMINATION_UNSUPPORTED", reasons);
        } else {
            check(offer.voucher() == null, "VOUCHER_MODE_REQUIRED", reasons);
        }
        return new EligibilityResult(reasons.isEmpty(), reasons);
    }

    private boolean supportedBenefit(Offer offer) {
        if ("VOUCHER_DISCOUNT".equals(offer.offerType())) return "VOUCHER".equals(offer.transactionMode());
        if ("VOUCHER".equals(offer.transactionMode())) return false;
        if (!Set.of("INSTANT_DISCOUNT", "PAYMENT_METHOD_DISCOUNT", "CASHBACK", "COUPON", "BANK_OFFER").contains(offer.offerType())) return false;
        var d = offer.discount();
        return d != null && Set.of("FLAT", "PERCENTAGE", "CASHBACK").contains(d.type()) && nonnegative(d.value())
                && (d.maximumDiscount() == null || nonnegative(d.maximumDiscount()))
                && (!"PERCENTAGE".equals(d.type()) || d.value().compareTo(new BigDecimal("100")) <= 0);
    }
    private boolean matches(List<String> allowed, String actual) {
        return allowed.isEmpty() || allowed.stream().anyMatch(value -> value.equalsIgnoreCase(actual));
    }
    private boolean positive(BigDecimal value) { return value != null && value.signum() > 0; }
    private boolean nonnegative(BigDecimal value) { return value != null && value.signum() >= 0; }
    private void check(boolean valid, String reason, List<String> reasons) { if (!valid) reasons.add(reason); }
}
