package com.paymentoptimizer.query.application;

import com.paymentoptimizer.query.domain.QueryUnderstandingException;
import java.text.Normalizer;
import java.util.Locale;
import org.springframework.stereotype.Component;

@Component
public class TextNormalizer {
    public String normalize(String raw) {
        if (raw == null || raw.isBlank() || raw.length() > 1000) {
            throw new QueryUnderstandingException("INVALID_QUERY", "Provide a purchase sentence of 1 to 1000 characters.");
        }
        return Normalizer.normalize(raw, Normalizer.Form.NFKC).toLowerCase(Locale.ROOT)
                .replaceAll("\\b(inr|rs\\.?|rupees)(?=[+-]?\\d)", "$1 ")
                .replaceAll("(?<=\\d)(inr|rs|rupees)\\b", " $1")
                .replaceAll("[^\\p{L}\\p{N}₹.,+\\-]", " ").replaceAll("\\s+", " ").strip();
    }
}
