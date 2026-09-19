package com.paymentoptimizer;

import static org.assertj.core.api.Assertions.*;
import static com.paymentoptimizer.OfferEligibilityTest.*;
import com.paymentoptimizer.offers.application.OfferEligibilityService;
import com.paymentoptimizer.offers.domain.Offer;
import com.paymentoptimizer.optimization.application.*;
import com.paymentoptimizer.optimization.domain.*;
import com.paymentoptimizer.query.domain.*;
import com.paymentoptimizer.wallet.domain.*;
import java.math.BigDecimal;
import java.util.*;
import org.junit.jupiter.api.Test;

class OptimizationEngineTest {
    final CostCalculator calculator = new CostCalculator();
    final RouteGenerator generator = new RouteGenerator(new OfferEligibilityService());
    RouteCandidate route(String id, Offer... offers) { return new RouteCandidate(id, "DIRECT", CARD, List.of(offers)); }

    @Test void separatesImmediatePaymentFromDeferredReward() {
        var cashback = new OfferExample(); cashback.key = "cashback"; cashback.type = "CASHBACK";
        cashback.discount = new Offer.Discount("FLAT", new BigDecimal("10"), null);
        var cost = calculator.calculate(PURCHASE, route("a", new OfferExample().build(), cashback.build())).cost();
        assertThat(cost.originalAmount()).isEqualTo(new BigDecimal("500.00"));
        assertThat(cost.eligibleAmount()).isEqualTo(new BigDecimal("500.00"));
        assertThat(cost.immediateDiscount()).isEqualTo(new BigDecimal("20.00"));
        assertThat(cost.payNow()).isEqualTo(new BigDecimal("480.00"));
        assertThat(cost.deferredReward()).isEqualTo(new BigDecimal("10.00"));
        assertThat(cost.effectiveCost()).isEqualTo(new BigDecimal("470.00"));
        assertThat(cost.saving()).isEqualTo(new BigDecimal("30.00"));
    }
    @Test void roundsHalfUpAndAppliesCapsWithoutNegativeCosts() {
        var offer = new OfferExample(); offer.discount = new Offer.Discount("PERCENTAGE", new BigDecimal("2.5"), null);
        var purchase = new PurchaseContext(Merchant.SWIGGY, PurchaseCategory.FOOD_DELIVERY, new BigDecimal("100.20"), BigDecimal.ONE);
        assertThat(calculator.calculate(purchase, route("round", offer.build())).cost().immediateDiscount()).isEqualTo(new BigDecimal("2.51"));
        offer.discount = new Offer.Discount("PERCENTAGE", new BigDecimal("50"), new BigDecimal("15"));
        assertThat(calculator.calculate(PURCHASE, route("cap", offer.build())).cost().immediateDiscount()).isEqualTo(new BigDecimal("15.00"));
        offer.discount = new Offer.Discount("FLAT", new BigDecimal("900"), null);
        var cashback = new OfferExample(); cashback.type = "CASHBACK";
        assertThat(calculator.calculate(PURCHASE, route("floor", offer.build(), cashback.build())).cost().effectiveCost()).isEqualTo(new BigDecimal("0.00"));
        assertThat(calculator.calculate(PURCHASE, route("floor", offer.build(), cashback.build())).cost().deferredReward()).isEqualTo(new BigDecimal("0.00"));
    }
    @Test void voucherPriceIsAuthoritativeAndRemainingPaymentIsIncluded() {
        var result = calculator.calculate(PURCHASE, new RouteCandidate("v", "VOUCHER", CARD, List.of(OfferExample.voucher("500", "487.50"))));
        assertThat(result.cost().payNow()).isEqualTo(new BigDecimal("487.50"));
        assertThat(result.cost().saving()).isEqualTo(new BigDecimal("12.50"));
        var partial = calculator.calculate(PURCHASE, new RouteCandidate("p", "VOUCHER", CARD, List.of(OfferExample.voucher("200", "190"))));
        assertThat(partial.cost().payNow()).isEqualTo(new BigDecimal("490.00"));
        assertThat(partial.cost().remainingPayment()).isEqualTo(new BigDecimal("300.00"));
        assertThat(partial.cost().eligibleAmount()).isEqualTo(new BigDecimal("200.00"));
        assertThatThrownBy(() -> calculator.calculate(PURCHASE, new RouteCandidate("bad", "VOUCHER", CARD,
                List.of(OfferExample.voucher("1000", "900"))))).isInstanceOf(IllegalArgumentException.class);
    }
    @Test void generatesDirectVoucherAndAllExplicitlyAllowedStacksBeforeRanking() {
        var second = new OfferExample(); second.key = "second";
        var generated = generator.generate(PURCHASE, new Wallet(List.of(CARD, CARD)),
                List.of(new OfferExample().build(), second.build(), OfferExample.voucher("500", "487.50")), OfferExample.NOW);
        assertThat(generated.candidates().stream().filter(r -> r.offers().isEmpty())).hasSize(2);
        assertThat(generated.candidates().stream().filter(RouteCandidate::voucher)).hasSize(2);
        assertThat(generated.candidates().stream().filter(r -> r.offers().size() == 2)).hasSize(1);
        var disallowed = new OfferExample(); disallowed.key = "not-stackable"; disallowed.stacking = "NOT_ALLOWED";
        var noStack = generator.generate(PURCHASE, new Wallet(List.of(CARD)), List.of(second.build(), disallowed.build()), OfferExample.NOW);
        assertThat(noStack.candidates()).noneMatch(r -> r.offers().size() > 1);
    }
    @Test void selectsDifferentWinnersForCashNowAndEffectiveCostAndIsOrderIndependent() {
        var instant = new OfferExample();
        var cashback = new OfferExample(); cashback.key = "cashback"; cashback.type = "CASHBACK";
        cashback.discount = new Offer.Discount("FLAT", new BigDecimal("30"), null);
        var routes = new ArrayList<>(List.of(calculator.calculate(PURCHASE, route("instant", instant.build())),
                calculator.calculate(PURCHASE, route("cashback", cashback.build())), calculator.calculate(PURCHASE, route("direct"))));
        var optimizer = new PaymentRouteOptimizer(); var result = optimizer.rank(routes);
        assertThat(result.bestEffectiveCostRoute().candidate().id()).isEqualTo("cashback");
        assertThat(result.bestPayNowRoute().candidate().id()).isEqualTo("instant");
        assertThat(result.alternatives()).extracting(r -> r.candidate().id()).containsExactly("direct");
        Collections.reverse(routes);
        assertThat(optimizer.rank(routes)).isEqualTo(result);
    }
    @Test void breaksTiesByPayNowThenConfidenceThenSimplicityThenStableId() {
        var optimizer = new PaymentRouteOptimizer();
        var discount = new OfferExample();
        var cashback = new OfferExample(); cashback.type = "CASHBACK";
        var instant = calculator.calculate(PURCHASE, route("z", discount.build()));
        var deferred = calculator.calculate(PURCHASE, route("a", cashback.build()));
        assertThat(optimizer.rank(List.of(deferred, instant)).bestEffectiveCostRoute()).isEqualTo(instant);
        discount.discount = new Offer.Discount("FLAT", BigDecimal.ZERO, null);
        var free = calculator.calculate(PURCHASE, route("offer", discount.build()));
        var plain = calculator.calculate(PURCHASE, route("z"));
        assertThat(optimizer.rank(List.of(free, plain)).bestEffectiveCostRoute()).isEqualTo(plain);
        discount.verification = "AMBIGUOUS";
        var unverified = calculator.calculate(PURCHASE, route("unverified", discount.build()));
        assertThat(optimizer.rank(List.of(unverified, free)).bestEffectiveCostRoute()).isEqualTo(free);
        var stable = calculator.calculate(PURCHASE, route("a"));
        assertThat(optimizer.rank(List.of(plain, stable)).bestEffectiveCostRoute()).isEqualTo(stable);
    }
}
