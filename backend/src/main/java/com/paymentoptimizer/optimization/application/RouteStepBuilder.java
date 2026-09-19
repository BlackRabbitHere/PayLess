package com.paymentoptimizer.optimization.application;

import com.paymentoptimizer.optimization.domain.*;
import com.paymentoptimizer.query.domain.PurchaseContext;
import com.paymentoptimizer.redirect.domain.ActionTarget;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class RouteStepBuilder {
    public List<RouteStep> build(PurchaseContext purchase, CalculatedRoute calculated) {
        var steps = new ArrayList<RouteStep>();
        var route = calculated.candidate();
        var open = switch (purchase.merchant()) {
            case SWIGGY -> ActionTarget.OPEN_SWIGGY;
            case YATRA -> ActionTarget.OPEN_YATRA;
            case EASEMYTRIP -> ActionTarget.OPEN_EASEMYTRIP;
        };
        String merchant = purchase.merchant().name();
        String payment = route.paymentInstrument().issuer() + " " + route.paymentInstrument().productName();
        if (route.voucher()) {
            var offer = route.offers().getFirst();
            if (!"GYFTR".equals(offer.provider()) || !"SWIGGY".equals(offer.merchant())) {
                throw new IllegalArgumentException("No approved voucher purchase destination.");
            }
            add(steps, "Buy INR " + calculated.cost().eligibleAmount().toPlainString() + " " + merchant
                    + " voucher for INR " + offer.voucher().sellingPrice().toPlainString() + " using " + payment,
                    "Buy Voucher", ActionTarget.BUY_SWIGGY_VOUCHER);
            add(steps, "Open " + merchant, "Open " + merchant, open);
            add(steps, "Redeem voucher at " + merchant + "; follow the provider's redemption terms.", null, null);
            add(steps, calculated.cost().remainingPayment().signum() > 0
                    ? "Complete remaining payment of INR " + calculated.cost().remainingPayment().toPlainString() + " using " + payment
                    : "Complete checkout; the voucher covers the purchase amount.", null, null);
        } else {
            add(steps, "Open " + merchant, "Open " + merchant, open);
            for (var offer : route.offers()) {
                if (offer.promoCode() != null && !offer.promoCode().isBlank()) add(steps, "Apply promo code " + offer.promoCode(), null, null);
            }
            add(steps, "Pay INR " + calculated.cost().payNow().toPlainString() + " using " + payment, null, null);
        }
        if (calculated.cost().deferredReward().signum() > 0) {
            add(steps, "Track INR " + calculated.cost().deferredReward().toPlainString() + " deferred reward under the offer terms; it does not reduce payment now.", null, null);
        }
        return List.copyOf(steps);
    }
    private void add(List<RouteStep> steps, String instruction, String label, ActionTarget target) {
        steps.add(new RouteStep(steps.size() + 1, instruction, label, target));
    }
}
