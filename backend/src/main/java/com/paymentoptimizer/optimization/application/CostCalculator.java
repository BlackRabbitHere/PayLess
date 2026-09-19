package com.paymentoptimizer.optimization.application;

import com.paymentoptimizer.offers.domain.Offer;
import com.paymentoptimizer.optimization.domain.*;
import com.paymentoptimizer.query.domain.PurchaseContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import org.springframework.stereotype.Service;

/** The sole monetary arithmetic authority. Voucher selling prices already include their advertised discount. */
@Service
public class CostCalculator {
    private static final BigDecimal ZERO = new BigDecimal("0.00");
    public CalculatedRoute calculate(PurchaseContext purchase, RouteCandidate route) {
        BigDecimal original = money(purchase.amount()), eligible = original, immediate = ZERO, deferred = ZERO, remaining = ZERO;
        if (route.voucher()) {
            if (route.offers().size() != 1) throw new IllegalArgumentException("A voucher route requires one priced voucher.");
            var voucher = route.offers().getFirst().voucher();
            if (voucher == null || voucher.faceValue() == null || voucher.sellingPrice() == null
                    || voucher.faceValue().signum() <= 0 || voucher.sellingPrice().signum() < 0
                    || voucher.faceValue().compareTo(original) > 0 || voucher.sellingPrice().compareTo(voucher.faceValue()) > 0) {
                throw new IllegalArgumentException("Invalid voucher pricing.");
            }
            eligible = money(voucher.faceValue());
            immediate = money(eligible.subtract(voucher.sellingPrice()));
            remaining = money(original.subtract(eligible));
        } else {
            for (Offer offer : route.offers()) {
                var benefit = benefit(offer.discount(), eligible);
                if ("CASHBACK".equals(offer.offerType()) || "CASHBACK".equals(offer.discount().type())) {
                    deferred = deferred.add(benefit);
                } else {
                    immediate = immediate.add(benefit);
                }
            }
            immediate = money(immediate.min(original));
        }
        var payNow = money(original.subtract(immediate));
        deferred = money(deferred.min(payNow));
        var effective = money(payNow.subtract(deferred));
        return new CalculatedRoute(route, new CostBreakdown(original, eligible, immediate, payNow, deferred,
                effective, money(original.subtract(effective)), remaining));
    }

    private BigDecimal benefit(Offer.Discount discount, BigDecimal base) {
        if (discount == null || discount.value() == null || discount.value().signum() < 0
                || (discount.maximumDiscount() != null && discount.maximumDiscount().signum() < 0)) {
            throw new IllegalArgumentException("Invalid benefit.");
        }
        BigDecimal result = switch (discount.type()) {
            case "PERCENTAGE" -> {
                if (discount.value().compareTo(new BigDecimal("100")) > 0) throw new IllegalArgumentException("Invalid rate.");
                yield base.multiply(discount.value()).divide(new BigDecimal("100"));
            }
            case "FLAT", "CASHBACK" -> discount.value();
            default -> throw new IllegalArgumentException("Unsupported benefit.");
        };
        if (discount.maximumDiscount() != null) result = result.min(discount.maximumDiscount());
        return money(result.min(base));
    }
    private BigDecimal money(BigDecimal value) { return value.setScale(2, RoundingMode.HALF_UP); }
}
