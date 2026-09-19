package com.paymentoptimizer.query.application;

import com.paymentoptimizer.query.domain.QueryUnderstandingException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.regex.Pattern;
import org.springframework.stereotype.Component;

@Component
public class AmountExtractor {
    private static final Pattern NUMBER = Pattern.compile("(?<![\\p{L}\\p{N}])[+-]?\\d[\\d,]*(?:\\.\\d+)?(?![\\p{L}\\p{N}])");
    private static final Pattern CURRENCY_BEFORE = Pattern.compile("(?:₹|\\b(?:rs\\.?|inr|rupees))\\s*$");
    private static final Pattern CURRENCY_AFTER = Pattern.compile("^\\s*(?:₹|(?:rs\\.?|inr|rupees)\\b)");
    private static final Pattern FORMAT = Pattern.compile("\\+?(?:\\d+|\\d{1,3}(?:,\\d{3})+|\\d{1,2}(?:,\\d{2})*,\\d{3})(?:\\.\\d{1,2})?");

    public BigDecimal extract(String text) {
        var numbers = NUMBER.matcher(text);
        var all = new ArrayList<String>();
        var marked = new ArrayList<String>();
        while (numbers.find()) {
            all.add(numbers.group());
            if (CURRENCY_BEFORE.matcher(text.substring(0, numbers.start())).find()
                    || CURRENCY_AFTER.matcher(text.substring(numbers.end())).find()) marked.add(numbers.group());
        }
        var candidates = marked.isEmpty() ? all : marked;
        if (candidates.size() != 1) {
            throw new QueryUnderstandingException(candidates.isEmpty() ? "AMOUNT_MISSING" : "AMOUNT_AMBIGUOUS",
                    "Specify exactly one purchase amount, using INR, Rs or ₹ when other numbers are present.");
        }
        var candidate = candidates.getFirst();
        if (!FORMAT.matcher(candidate).matches()) throw invalidAmount();
        var amount = new BigDecimal(candidate.replace(",", "")).setScale(2, RoundingMode.UNNECESSARY);
        if (amount.signum() <= 0 || amount.precision() > 18) throw invalidAmount();
        return amount;
    }

    private QueryUnderstandingException invalidAmount() {
        return new QueryUnderstandingException("AMOUNT_INVALID", "Use a positive INR amount with at most two decimal places.");
    }
}
