package com.paymentoptimizer.travel.application;

import com.paymentoptimizer.query.domain.Merchant;
import com.paymentoptimizer.travel.domain.*;
import java.math.BigDecimal;
import java.util.List;
import org.springframework.stereotype.Component;

@Component
public class DemoFareProvider implements FareProvider {
    @Override public List<FareOption> search(TravelSearch search) {
        // One identical illustrative flight across two booking providers; no live availability is implied.
        if (!List.of(search.origin(), search.destination()).containsAll(List.of("Delhi", "Mumbai"))) return List.of();
        return List.of(fare(search, Merchant.YATRA, "5650.00"), fare(search, Merchant.EASEMYTRIP, "5459.00"));
    }
    private FareOption fare(TravelSearch search, Merchant merchant, String perPassenger) {
        return new FareOption("demo-" + merchant.name().toLowerCase(java.util.Locale.ROOT), merchant,
                search.origin(), search.destination(), search.departureDate(), search.passengers(), "Demo flight RW101 · Economy",
                new BigDecimal(perPassenger).multiply(BigDecimal.valueOf(search.passengers())), "INR", true, "DemoFareProvider");
    }
}
