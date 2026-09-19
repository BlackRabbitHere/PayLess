package com.paymentoptimizer.offers.application;

import com.paymentoptimizer.query.domain.Merchant;
import java.util.List;
import org.springframework.stereotype.Component;

/** Only providers that actually support the requested merchant may be queried. */
@Component
public class OfferProviderCatalog {
    public List<String> providersFor(Merchant merchant) {
        return switch (merchant) {
            case SWIGGY -> List.of("GYFTR");
            case YATRA -> List.of("YATRA");
            case EASEMYTRIP -> List.of("EASEMYTRIP");
        };
    }
}
