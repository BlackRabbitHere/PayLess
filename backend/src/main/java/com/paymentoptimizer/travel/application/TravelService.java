package com.paymentoptimizer.travel.application;

import com.paymentoptimizer.optimization.application.OptimizationService;
import com.paymentoptimizer.optimization.application.OptimizationService.PurchaseOption;
import com.paymentoptimizer.query.domain.*;
import com.paymentoptimizer.travel.domain.FareProvider;
import com.paymentoptimizer.travel.dto.*;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class TravelService {
    private final FareProvider fares;
    private final OptimizationService optimization;
    public TravelService(FareProvider fares, OptimizationService optimization) {
        this.fares = fares; this.optimization = optimization;
    }
    public TravelResponse optimize(TravelRequest request) {
        var options = fares.search(request.toSearch());
        if (options.isEmpty()) return new TravelResponse(List.of(), null, Map.of(),
                List.of("No fares available for this search. The demo fare source supports Delhi–Mumbai in both directions."));
        var result = optimization.optimizeOptions(options.stream().map(f -> new PurchaseOption(f.id(),
                new PurchaseContext(f.merchant(), PurchaseCategory.TRAVEL, f.totalAmount(), BigDecimal.ONE))).toList(), request.toWallet());
        return new TravelResponse(options, result.optimization(), result.routeOptionIds(),
                options.stream().anyMatch(f -> f.demo()) ? List.of("DEMO_FARES: Illustrative fares, including mandatory fees for all passengers. Confirm availability and the final price with the booking provider.") : List.of());
    }
}
