package com.paymentoptimizer.query.domain;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

public record PurchaseContext(Merchant merchant, PurchaseCategory category, BigDecimal amount,
        BigDecimal confidence) {
    public PurchaseContext {
        Objects.requireNonNull(merchant);
        Objects.requireNonNull(category);
        Objects.requireNonNull(amount);
        Objects.requireNonNull(confidence);
        amount = amount.setScale(2, RoundingMode.UNNECESSARY);
        if (amount.signum() <= 0 || amount.precision() > 18) throw new IllegalArgumentException("Invalid purchase amount.");
        if (confidence.signum() < 0 || confidence.compareTo(BigDecimal.ONE) > 0) {
            throw new IllegalArgumentException("Invalid confidence.");
        }
    }
}
