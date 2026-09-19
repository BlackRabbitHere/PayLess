package com.paymentoptimizer.query.application;

import com.paymentoptimizer.query.domain.PurchaseContext;
import org.springframework.stereotype.Service;

@Service
public class QueryUnderstandingService {
    private final TextNormalizer normalizer;
    private final AmountExtractor amounts;
    private final MerchantMatcher merchants;
    private final CategoryResolver categories;

    public QueryUnderstandingService(TextNormalizer normalizer, AmountExtractor amounts,
            MerchantMatcher merchants, CategoryResolver categories) {
        this.normalizer = normalizer;
        this.amounts = amounts;
        this.merchants = merchants;
        this.categories = categories;
    }

    public PurchaseContext understand(String sentence) {
        var text = normalizer.normalize(sentence);
        var amount = amounts.extract(text);
        var match = merchants.match(text);
        return new PurchaseContext(match.merchant(), categories.resolve(match.merchant()), amount, match.confidence());
    }
}
