package com.paymentoptimizer.optimization.dto;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.NotNull;

public record ScraperCheckRequest(@NotNull Provider provider, @NotNull Merchant merchant) {
    public enum Provider { GYFTR, YATRA, EASEMYTRIP }
    public enum Merchant { SWIGGY, YATRA, EASEMYTRIP }

    @AssertTrue(message = "Unsupported provider/merchant pair")
    public boolean isSupportedPair() {
        return provider != null && merchant != null && switch (provider) {
            case GYFTR -> merchant == Merchant.SWIGGY;
            case YATRA -> merchant == Merchant.YATRA;
            case EASEMYTRIP -> merchant == Merchant.EASEMYTRIP;
        };
    }
}
