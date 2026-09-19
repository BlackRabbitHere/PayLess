package com.paymentoptimizer.optimization.dto;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

/** Application-owned preview, deliberately different from the scraper wire contract. */
public record ScraperCheckResponse(UUID requestId, String status, String provider, String merchant,
        boolean fixture, List<OfferPreview> observations, List<String> warningCodes, List<String> errorCodes) {
    public record OfferPreview(String id, String title, String verificationStatus, String voucherFaceValue,
            String voucherSellingPrice, String discountValue, String maximumDiscount,
            String sourceUrl, Instant observedAt) {}
}
