package com.paymentoptimizer.integration.scraper.dto;

import java.math.BigDecimal;
import java.net.URI;
import java.time.Instant;
import java.util.List;

public record ScrapedOfferDto(Integer schemaVersion, String externalKey, String provider, String merchant,
        String title, String offerType, String transactionMode, Voucher voucher, Discount discount,
        BigDecimal minimumTransaction, List<String> eligibleIssuers, List<String> eligibleInstrumentTypes,
        String promoCode, Instant validFrom, Instant validUntil, String usageLimit, String stackingPolicy,
        List<String> terms, String availability, URI sourceUrl, URI actionUrl, String actionLabel,
        String verificationStatus, Instant lastVerifiedAt, Instant scrapedAt, String contentHash) {
    public record Voucher(BigDecimal faceValue, BigDecimal sellingPrice) {}
    public record Discount(String type, BigDecimal value, BigDecimal maximumDiscount) {}
}
