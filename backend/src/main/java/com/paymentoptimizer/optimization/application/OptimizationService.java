package com.paymentoptimizer.optimization.application;

import com.paymentoptimizer.offers.application.OfferAcquisitionService;
import com.paymentoptimizer.offers.domain.*;
import com.paymentoptimizer.optimization.domain.CalculatedRoute;
import com.paymentoptimizer.optimization.domain.RouteCandidate;
import com.paymentoptimizer.optimization.dto.*;
import com.paymentoptimizer.query.application.QueryUnderstandingService;
import com.paymentoptimizer.query.domain.PurchaseContext;
import com.paymentoptimizer.query.domain.Merchant;
import com.paymentoptimizer.wallet.domain.Wallet;
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
        return optimizeOptions(List.of(new PurchaseOption("", context)), request.toWallet()).optimization();
    }

    /** A priced purchase enters the same engine whether supplied by query parsing or a fare provider. */
    public record PurchaseOption(String id, PurchaseContext context) {}
    public record Selection(OptimizeResponse optimization, Map<String, String> routeOptionIds) {}

    public Selection optimizeOptions(List<PurchaseOption> options, Wallet wallet) {
        if (options.isEmpty()) throw new IllegalArgumentException("At least one priced purchase is required.");
        var acquired = new LinkedHashMap<Merchant, List<OfferBatch>>();
        var contexts = new HashMap<String, PurchaseContext>();
        var optionIds = new LinkedHashMap<String, String>();
        var candidates = new ArrayList<CalculatedRoute>();
        var assessments = new ArrayList<RouteGenerator.Assessment>();
        for (var option : options) {
            var context = option.context();
            var sources = acquired.computeIfAbsent(context.merchant(), ignored -> acquisition.acquireAvailable(context));
            var generated = generator.generate(context, wallet, sources.stream().flatMap(b -> b.offers().stream()).toList(), clock.instant());
            assessments.addAll(generated.eligibility());
            for (var candidate : generated.candidates()) {
                String id = option.id().isEmpty() ? candidate.id() : option.id() + ":" + candidate.id();
                var identified = new RouteCandidate(id, candidate.kind(), candidate.paymentInstrument(), candidate.offers());
                candidates.add(costs.calculate(context, identified));
                contexts.put(id, context);
                optionIds.put(id, option.id());
            }
        }
        var batches = acquired.values().stream().flatMap(List::stream).toList();
        var warnings = new ArrayList<String>();
        if (batches.stream().allMatch(b -> "UNAVAILABLE".equals(b.status()))) {
            warnings.add("Live offer acquisition unavailable. Direct payment routes are still returned.");
        }
        for (var batch : batches) {
            if (batch.fixture()) warnings.add("FIXTURE_DATA: " + batch.provider() + " offers are synthetic, not live commercial offers.");
            batch.warnings().forEach(w -> warnings.add(w.code() + ": " + w.message()));
            batch.errors().forEach(e -> warnings.add(e.code() + ": Offer acquisition incomplete for " + batch.provider() + "."));
        }
        var ranked = optimizer.rank(candidates);
        if (assessments.stream().anyMatch(a -> !a.result().eligible())) {
            warnings.add("Some verified offers are ineligible or have unconfirmed restrictions; see eligibility reasons.");
        }
        warnings.add("Direct payment assumes UPI is available and that the supplied wallet metadata is accurate. No unpriced fees or wallet rewards are assumed.");
        var context = contexts.get(ranked.bestEffectiveCostRoute().candidate().id());
        return new Selection(new OptimizeResponse(context, "INR", present(context, ranked.bestEffectiveCostRoute(), batches),
                present(contexts.get(ranked.bestPayNowRoute().candidate().id()), ranked.bestPayNowRoute(), batches),
                ranked.alternatives().stream().map(r -> present(contexts.get(r.candidate().id()), r, batches)).toList(),
                assessments.stream().distinct().toList(), batches.stream().map(b -> new OptimizeResponse.Acquisition(b.requestId(), b.provider(), b.status(),
                        b.fixture(), b.warnings(), b.errors())).toList(), warnings.stream().distinct().toList()), Map.copyOf(optionIds));
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
