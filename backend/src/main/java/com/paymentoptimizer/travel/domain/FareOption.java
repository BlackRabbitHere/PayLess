package com.paymentoptimizer.travel.domain;

import com.paymentoptimizer.query.domain.Merchant;
import java.math.BigDecimal;
import java.time.LocalDate;

/** Total quoted amount for all passengers, including the demo provider's mandatory fees. */
public record FareOption(String id, Merchant merchant, String origin, String destination,
        LocalDate departureDate, int passengers, String flight, BigDecimal totalAmount, String currency,
        boolean demo, String fareSource) {}
