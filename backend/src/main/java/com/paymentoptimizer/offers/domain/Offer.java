package com.paymentoptimizer.offers.domain;

import java.math.BigDecimal;
import java.net.URI;
import java.time.Instant;
import java.util.List;

/** Stable application offer. Verification is source consistency, not purchase eligibility. */
public record Offer(String externalKey, String provider, String merchant, String title,
        String offerType, String transactionMode, Voucher voucher, Discount discount,
        BigDecimal minimumTransaction, List<String> eligibleIssuers, List<String> eligibleInstrumentTypes,
        String promoCode, Instant validFrom, Instant validUntil, String usageLimit, String stackingPolicy,
        List<String> terms, String availability, URI sourceUrl, URI actionUrl, String actionLabel,
        String verificationStatus, Instant lastVerifiedAt, Instant observedAt, String contentHash) {
    public Offer {
        eligibleIssuers = List.copyOf(eligibleIssuers);
        eligibleInstrumentTypes = List.copyOf(eligibleInstrumentTypes);
        terms = List.copyOf(terms);
    }
    public record Voucher(BigDecimal faceValue, BigDecimal sellingPrice) {}
    public record Discount(String type, BigDecimal value, BigDecimal maximumDiscount) {}
}
