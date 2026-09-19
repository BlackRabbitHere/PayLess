package com.paymentoptimizer;

import static org.assertj.core.api.Assertions.*;
import com.paymentoptimizer.query.application.*;
import com.paymentoptimizer.query.domain.*;
import java.math.BigDecimal;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class QueryUnderstandingTest {
    private final QueryUnderstandingService queries = new QueryUnderstandingService(
            new TextNormalizer(), new AmountExtractor(), new MerchantMatcher(), new CategoryResolver());

    @Test
    void understandsThePhaseTwoCheckpointDeterministically() {
        var context = queries.understand("I am paying 500 rs on swigy");
        assertThat(context).isEqualTo(new PurchaseContext(Merchant.SWIGGY, PurchaseCategory.FOOD_DELIVERY,
                new BigDecimal("500.00"), new BigDecimal("0.96")));
        assertThat(queries.understand("I am ordering food on swigy for 500 rs")).isEqualTo(context);
    }

    @ParameterizedTest
    @CsvSource(value = {
        "Pay ₹500.25 on SWIGGY!|SWIGGY|FOOD_DELIVERY|500.25|1.00",
        "Pay 500rs on swiggy|SWIGGY|FOOD_DELIVERY|500.00|1.00",
        "Pay INR500 on swiggy|SWIGGY|FOOD_DELIVERY|500.00|1.00",
        "pay rs. 500 on swiggy money|SWIGGY|FOOD_DELIVERY|500.00|1.00",
        "Book ease my trip for INR 1,25,000.50|EASEMYTRIP|TRAVEL|125000.50|0.96",
        "I have 2 tickets on yatra for 5000 rs|YATRA|TRAVEL|5000.00|1.00",
        "500 on swiggi|SWIGGY|FOOD_DELIVERY|500.00|0.85",
        "500 on yattra|YATRA|TRAVEL|500.00|0.85",
        "500 on easemytrp|EASEMYTRIP|TRAVEL|500.00|0.85",
        "５００ on ＳＷＩＧＧＹ|SWIGGY|FOOD_DELIVERY|500.00|1.00"
    }, delimiter = '|')
    void understandsMoneyAliasesFuzzyNamesAndUnicode(String sentence, Merchant merchant,
            PurchaseCategory category, String amount, String confidence) {
        var context = queries.understand(sentence);
        assertThat(context.merchant()).isEqualTo(merchant);
        assertThat(context.category()).isEqualTo(category);
        assertThat(context.amount().toPlainString()).isEqualTo(amount);
        assertThat(context.confidence()).isEqualByComparingTo(confidence);
    }

    @ParameterizedTest
    @CsvSource(value = {
        "swiggy|AMOUNT_MISSING", "500 or 600 on swiggy|AMOUNT_AMBIGUOUS",
        "500 rs or 600 rs on swiggy|AMOUNT_AMBIGUOUS", "0 on swiggy|AMOUNT_INVALID",
        "-500 on swiggy|AMOUNT_INVALID", "500.123 on swiggy|AMOUNT_INVALID",
        "1,2,50 on swiggy|AMOUNT_INVALID", "10000000000000000 on swiggy|AMOUNT_INVALID",
        "500 on unknownshop|MERCHANT_UNSUPPORTED", "500 on swiggy and yatra|MERCHANT_AMBIGUOUS",
        "500 on swigy and yatra|MERCHANT_AMBIGUOUS", "500 on swiggi or yattra|MERCHANT_AMBIGUOUS",
        "500 on swiggystore|MERCHANT_UNSUPPORTED"
    }, delimiter = '|')
    void requestsClarificationInsteadOfGuessing(String sentence, String code) {
        assertThatThrownBy(() -> queries.understand(sentence)).isInstanceOfSatisfying(QueryUnderstandingException.class,
                error -> assertThat(error.code()).isEqualTo(code));
    }

    @Test
    void rejectsEmptyAndOversizedQueries() {
        assertThatThrownBy(() -> queries.understand(null)).isInstanceOf(QueryUnderstandingException.class);
        assertThatThrownBy(() -> queries.understand(" ")).isInstanceOf(QueryUnderstandingException.class);
        assertThatThrownBy(() -> queries.understand("x".repeat(1001))).isInstanceOf(QueryUnderstandingException.class);
    }
}
