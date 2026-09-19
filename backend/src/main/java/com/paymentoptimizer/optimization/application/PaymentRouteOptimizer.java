package com.paymentoptimizer.optimization.application;

import com.paymentoptimizer.optimization.domain.CalculatedRoute;
import java.util.*;
import org.springframework.stereotype.Service;

@Service
public class PaymentRouteOptimizer {
    private static final Comparator<CalculatedRoute> EFFECTIVE = Comparator
            .comparing((CalculatedRoute r) -> r.cost().effectiveCost())
            .thenComparing(r -> r.cost().payNow())
            .thenComparing(Comparator.comparingInt((CalculatedRoute r) -> r.candidate().verificationConfidence()).reversed())
            .thenComparingInt(r -> r.candidate().complexity()).thenComparing(r -> r.candidate().id());
    public record Ranking(CalculatedRoute bestEffectiveCostRoute, CalculatedRoute bestPayNowRoute,
            List<CalculatedRoute> alternatives) {
        public Ranking { alternatives = List.copyOf(alternatives); }
    }
    public Ranking rank(List<CalculatedRoute> routes) {
        if (routes.isEmpty()) throw new IllegalArgumentException("At least one calculated route is required.");
        var sorted = routes.stream().sorted(EFFECTIVE).toList();
        var effective = sorted.getFirst();
        var payNow = routes.stream().min(Comparator.comparing((CalculatedRoute r) -> r.cost().payNow()).thenComparing(EFFECTIVE)).orElseThrow();
        return new Ranking(effective, payNow, sorted.stream().filter(r -> !r.candidate().id().equals(effective.candidate().id())
                && !r.candidate().id().equals(payNow.candidate().id())).toList());
    }
}
