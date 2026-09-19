package com.paymentoptimizer.query.application;

import com.paymentoptimizer.query.domain.Merchant;
import com.paymentoptimizer.query.domain.PurchaseCategory;
import org.springframework.stereotype.Component;

@Component
public class CategoryResolver {
    public PurchaseCategory resolve(Merchant merchant) {
        return switch (merchant) {
            case SWIGGY -> PurchaseCategory.FOOD_DELIVERY;
            case YATRA, EASEMYTRIP -> PurchaseCategory.TRAVEL;
        };
    }
}
