package com.paymentoptimizer.travel.dto;

import com.paymentoptimizer.optimization.dto.OptimizeResponse;
import com.paymentoptimizer.travel.domain.FareOption;
import java.util.List;
import java.util.Map;

public record TravelResponse(List<FareOption> fares, OptimizeResponse optimization,
        Map<String, String> routeFareIds, List<String> warnings) {}
