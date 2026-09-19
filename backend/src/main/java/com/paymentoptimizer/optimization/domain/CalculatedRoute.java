package com.paymentoptimizer.optimization.domain;

import java.util.Objects;

public record CalculatedRoute(RouteCandidate candidate, CostBreakdown cost) {
    public CalculatedRoute { Objects.requireNonNull(candidate); Objects.requireNonNull(cost); }
}
