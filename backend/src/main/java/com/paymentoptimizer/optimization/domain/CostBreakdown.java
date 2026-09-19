package com.paymentoptimizer.optimization.domain;

import java.math.BigDecimal;

public record CostBreakdown(BigDecimal originalAmount, BigDecimal eligibleAmount, BigDecimal immediateDiscount,
        BigDecimal payNow, BigDecimal deferredReward, BigDecimal effectiveCost, BigDecimal saving,
        BigDecimal remainingPayment) {}
