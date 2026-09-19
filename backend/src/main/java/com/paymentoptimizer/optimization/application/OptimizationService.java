package com.paymentoptimizer.optimization.application;

import com.paymentoptimizer.offers.application.OfferAcquisitionService;
import com.paymentoptimizer.offers.domain.*;
import com.paymentoptimizer.optimization.domain.CalculatedRoute;
import com.paymentoptimizer.optimization.dto.*;
import com.paymentoptimizer.query.application.QueryUnderstandingService;
import com.paymentoptimizer.query.domain.PurchaseContext;
import com.paymentoptimizer.redirect.application.RedirectSafetyValidator;
import java.time.Clock;
import java.util.*;
import org.springframework.stereotype.Service;

@Service
public class OptimizationService {
    private final QueryUnderstandingService queries;
    private final OfferAcquisitionService acquisition;
    private final RouteGenerator generator;
    private final CostCalculator costs;
    private final PaymentRouteOptimizer optimizer;
    private final RouteStepBuilder steps;
    private final RedirectSafetyValidator redirects;
    private final Clock clock;

    public OptimizationService(QueryUnderstandingService queries, OfferAcquisitionService acquisition,
            RouteGenerator generator, CostCalculator costs, PaymentRouteOptimizer optimizer, RouteStepBuilder steps,
            RedirectSafetyValidator redirects, Clock clock) {
        this.queries = queries; this.acquisition = acquisition; this.generator = generator; this.costs = costs;
        this.optimizer = optimizer; this.steps = steps; this.redirects = redirects; this.clock = clock;
    }
    public OptimizeResponse optimize(OptimizeRequest request) {
        var context = queries.understand(request.query());
        var batches = acquisition.acquireAvailable(context);
        var warnings = new ArrayList<String>();
        if (batches.stream().allMatch(b -> "UNAVAILABLE".equals(b.status()))) {
            warnings.add("Live offer acquisition unavailable. Direct payment routes are still returned.");
        }
        for (var batch : batches) {
            if (batch.fixture()) warnings.add("FIXTURE_DATA: " + batch.provider() + " offers are synthetic, not live commercial offers.");
            batch.warnings().forEach(w -> warnings.add(w.code() + ": " + w.message()));
            batch.errors().forEach(e -> warnings.add(e.code() + ": Offer acquisition incomplete for " + batch.provider() + "."));
        }
        var offers = batches.stream().flatMap(b -> b.offers().stream()).toList();
        var generated = generator.generate(context, request.toWallet(), offers, clock.instant());
        var ranked = optimizer.rank(generated.candidates().stream().map(r -> costs.calculate(context, r)).toList());
        if (generated.eligibility().stream().anyMatch(a -> !a.result().eligible())) {
            warnings.add("Some verified offers are ineligible or have unconfirmed restrictions; see eligibility reasons.");
        }
        warnings.add("Direct payment assumes UPI is available and that the supplied wallet metadata is accurate. No unpriced fees or wallet rewards are assumed.");
        return new OptimizeResponse(context, "INR", present(context, ranked.bestEffectiveCostRoute(), batches),
                present(context, ranked.bestPayNowRoute(), batches), ranked.alternatives().stream().map(r -> present(context, r, batches)).toList(),
                generated.eligibility(), batches.stream().map(b -> new OptimizeResponse.Acquisition(b.requestId(), b.provider(), b.status(),
                        b.fixture(), b.warnings(), b.errors())).toList(), warnings.stream().distinct().toList());
    }
    private OptimizeResponse.Route present(PurchaseContext context, CalculatedRoute route, List<OfferBatch> batches) {
        var warnings = new ArrayList<String>();
        var metadata = route.candidate().offers().stream().map(offer -> {
            if (offer.validFrom() == null || offer.validUntil() == null) warnings.add("Offer validity bounds were not fully published; confirm before paying.");
            if (offer.usageLimit() == null) warnings.add("No usage rule was published; confirm the provider's terms before paying.");
            if (offer.eligibleNetworks().isEmpty()) warnings.add("No structured network restriction was supplied; check the source terms.");
            boolean fixture = batches.stream().anyMatch(b -> b.fixture() && b.offers().contains(offer));
            return OptimizeResponse.SourceMetadata.from(offer, fixture);
        }).toList();
        return new OptimizeResponse.Route(route.candidate().id(), route.candidate().kind(), route.candidate().paymentInstrument(),
                route.cost(), route.candidate().verificationConfidence(), route.candidate().complexity(),
                steps.build(context, route).stream().map(s -> new OptimizeResponse.Step(s.number(), s.instruction(), s.actionLabel(),
                        s.actionTarget() == null ? null : redirects.validate(s.actionTarget()))).toList(), metadata, warnings.stream().distinct().toList());
    }
}
