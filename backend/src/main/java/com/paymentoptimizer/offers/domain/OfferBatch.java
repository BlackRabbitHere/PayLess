package com.paymentoptimizer.offers.domain;

import java.util.List;
import java.util.UUID;

public record OfferBatch(UUID requestId, String status, String provider, String merchant, boolean fixture,
        List<Offer> offers, List<Notice> warnings, List<Failure> errors) {
    public OfferBatch {
        offers = List.copyOf(offers);
        warnings = List.copyOf(warnings);
        errors = List.copyOf(errors);
    }
    public record Notice(String code, String message, String externalKey) {}
    public record Failure(String code, String message, String provider, boolean retryable) {}
}
