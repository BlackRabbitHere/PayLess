package com.paymentoptimizer.query.application;

import com.paymentoptimizer.query.domain.Merchant;
import com.paymentoptimizer.query.domain.QueryUnderstandingException;
import java.math.BigDecimal;
import java.util.EnumSet;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import org.springframework.stereotype.Component;

@Component
public class MerchantMatcher {
    private static final Map<String, Merchant> EXACT = Map.of(
            "swiggy", Merchant.SWIGGY, "yatra", Merchant.YATRA, "easemytrip", Merchant.EASEMYTRIP);
    private static final Map<String, Merchant> ALIASES = Map.of(
            "swigy", Merchant.SWIGGY, "swiggy money", Merchant.SWIGGY,
            "ease my trip", Merchant.EASEMYTRIP, "emt", Merchant.EASEMYTRIP);

    public record Match(Merchant merchant, BigDecimal confidence) {}

    public Match match(String text) {
        var exact = matches(text, EXACT);
        var aliases = matches(text, ALIASES);
        var recognized = EnumSet.noneOf(Merchant.class);
        recognized.addAll(exact);
        recognized.addAll(aliases);
        if (recognized.size() > 1) throw ambiguous();
        if (!exact.isEmpty()) return new Match(exact.iterator().next(), new BigDecimal("1.00"));
        if (!aliases.isEmpty()) return new Match(aliases.iterator().next(), new BigDecimal("0.96"));

        var fuzzy = EnumSet.noneOf(Merchant.class);
        for (String word : text.split("[^a-z]+")) {
            if (word.length() < 4) continue;
            EXACT.forEach((name, merchant) -> {
                // One edit for short names, two only for long names; no LLM or network calls.
                if (distance(word, name) <= (name.length() >= 8 ? 2 : 1)) fuzzy.add(merchant);
            });
        }
        if (fuzzy.size() > 1) throw ambiguous();
        if (fuzzy.isEmpty()) throw new QueryUnderstandingException("MERCHANT_UNSUPPORTED", "Specify Swiggy, Yatra or EaseMyTrip.");
        return new Match(fuzzy.iterator().next(), new BigDecimal("0.85"));
    }

    private Set<Merchant> matches(String text, Map<String, Merchant> names) {
        var found = EnumSet.noneOf(Merchant.class);
        names.forEach((name, merchant) -> {
            if (Pattern.compile("(?<![a-z0-9])" + Pattern.quote(name) + "(?![a-z0-9])").matcher(text).find()) found.add(merchant);
        });
        return found;
    }

    private QueryUnderstandingException ambiguous() {
        return new QueryUnderstandingException("MERCHANT_AMBIGUOUS", "Specify one merchant per purchase.");
    }

    private int distance(String left, String right) {
        int[] previous = new int[right.length() + 1];
        for (int j = 0; j <= right.length(); j++) previous[j] = j;
        for (int i = 1; i <= left.length(); i++) {
            int[] current = new int[right.length() + 1];
            current[0] = i;
            for (int j = 1; j <= right.length(); j++) {
                current[j] = Math.min(Math.min(current[j - 1] + 1, previous[j] + 1),
                        previous[j - 1] + (left.charAt(i - 1) == right.charAt(j - 1) ? 0 : 1));
            }
            previous = current;
        }
        return previous[right.length()];
    }
}
