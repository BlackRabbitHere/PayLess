package com.paymentoptimizer;

import static org.assertj.core.api.Assertions.assertThat;
import com.paymentoptimizer.offers.application.OfferEligibilityService;
import com.paymentoptimizer.query.domain.*;
import com.paymentoptimizer.wallet.domain.WalletInstrument;
import com.paymentoptimizer.wallet.domain.WalletInstrument.*;
import java.math.BigDecimal;
import java.util.*;
import java.util.function.Consumer;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.*;

class OfferEligibilityTest {
    static final PurchaseContext PURCHASE = new PurchaseContext(Merchant.SWIGGY, PurchaseCategory.FOOD_DELIVERY, new BigDecimal("500"), BigDecimal.ONE);
    static final WalletInstrument CARD = new WalletInstrument("HDFC", "Millennia", InstrumentType.CREDIT_CARD, Network.VISA);
    final OfferEligibilityService service = new OfferEligibilityService();

    static Stream<Arguments> restrictions() {
        return Stream.of(
                rule("MERCHANT_MISMATCH", o -> o.merchant = "YATRA"),
                rule("ISSUER_MISMATCH", o -> o.issuers = List.of("ICICI")),
                rule("CARD_TYPE_MISMATCH", o -> o.instruments = List.of("DEBIT_CARD")),
                rule("NETWORK_MISMATCH", o -> o.networks = List.of("RUPAY")),
                rule("TRANSACTION_MODE_MISMATCH", o -> o.mode = "EMI"),
                rule("MINIMUM_TRANSACTION_NOT_MET", o -> o.minimum = new BigDecimal("500.01")),
                rule("OFFER_NOT_STARTED", o -> o.from = OfferExample.NOW.plusSeconds(1)),
                rule("OFFER_EXPIRED", o -> o.until = OfferExample.NOW.minusSeconds(1)),
                rule("USAGE_RULE_UNCONFIRMED", o -> o.usage = "Once per card during the offer period."),
                rule("OFFER_NOT_VERIFIED", o -> o.verification = "AMBIGUOUS"),
                rule("AVAILABILITY_UNCONFIRMED", o -> o.availability = "UNKNOWN"),
                rule("UNSUPPORTED_BENEFIT", o -> o.discount = new com.paymentoptimizer.offers.domain.Offer.Discount("VARIABLE", null, null)));
    }
    static Arguments rule(String reason, Consumer<OfferExample> change) { return Arguments.of(reason, change); }
    @ParameterizedTest @MethodSource("restrictions")
    void rejectsEachRestrictionIndependently(String reason, Consumer<OfferExample> change) {
        var offer = new OfferExample(); change.accept(offer);
        var result = service.evaluate(offer.build(), PURCHASE, CARD, "CARD", List.of(), OfferExample.NOW);
        assertThat(result.eligible()).isFalse();
        assertThat(result.reasons()).containsExactly(reason);
    }
    @Test void collectsAllReasonsAndIncludesExactValidityAndMinimumBoundaries() {
        var offer = new OfferExample(); offer.minimum = new BigDecimal("500"); offer.from = OfferExample.NOW; offer.until = OfferExample.NOW;
        assertThat(service.evaluate(offer.build(), PURCHASE, CARD, "CARD", List.of(), OfferExample.NOW).eligible()).isTrue();
        offer.issuers = List.of("ICICI"); offer.networks = List.of("RUPAY");
        assertThat(service.evaluate(offer.build(), PURCHASE, CARD, "CARD", List.of(), OfferExample.NOW).reasons())
                .containsExactly("ISSUER_MISMATCH", "NETWORK_MISMATCH");
    }
    @Test void unknownStackingAllowsSingleUseButNeverStackingOrDuplicateOffers() {
        var offer = new OfferExample(); offer.stacking = "UNKNOWN";
        assertThat(service.evaluate(offer.build(), PURCHASE, CARD, "CARD", List.of(), OfferExample.NOW).eligible()).isTrue();
        assertThat(service.evaluate(offer.build(), PURCHASE, CARD, "CARD", List.of(offer.build()), OfferExample.NOW).reasons())
                .contains("STACKING_NOT_ALLOWED", "DUPLICATE_OFFER");
    }
    @Test void recognizesCreditCardModeAndGenericCardRestrictions() {
        var offer = new OfferExample(); offer.mode = "CREDIT_CARD"; offer.instruments = List.of("CARD");
        assertThat(service.evaluate(offer.build(), PURCHASE, CARD, "CARD", List.of(), OfferExample.NOW).eligible()).isTrue();
    }
    @Test void voucherMinimumUsesActualVoucherPaymentAndOversizedVouchersAreExcluded() {
        var offer = new OfferExample(); offer.mode = "VOUCHER"; offer.type = "VOUCHER_DISCOUNT";
        offer.voucher = new com.paymentoptimizer.offers.domain.Offer.Voucher(new BigDecimal("500"), new BigDecimal("480"));
        offer.minimum = new BigDecimal("490");
        assertThat(service.evaluate(offer.build(), PURCHASE, CARD, "VOUCHER", List.of(), OfferExample.NOW).reasons())
                .containsExactly("MINIMUM_TRANSACTION_NOT_MET");
        assertThat(service.evaluate(OfferExample.voucher("1000", "980"), PURCHASE, CARD, "VOUCHER", List.of(), OfferExample.NOW).reasons())
                .contains("VOUCHER_DENOMINATION_UNSUPPORTED");
    }
}
