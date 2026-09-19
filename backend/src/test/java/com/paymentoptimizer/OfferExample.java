package com.paymentoptimizer;

import com.paymentoptimizer.offers.domain.Offer;
import java.math.BigDecimal;
import java.net.URI;
import java.time.Instant;
import java.util.List;

/** Synthetic domain examples only; never used by application code. */
class OfferExample {
    static final Instant NOW = Instant.parse("2026-09-19T12:00:00Z");
    String key = "offer", merchant = "SWIGGY", provider = "GYFTR", type = "INSTANT_DISCOUNT", mode = "CARD";
    String usage = "UNLIMITED", stacking = "ALLOWED", availability = "AVAILABLE", verification = "VERIFIED";
    List<String> issuers = List.of(), instruments = List.of(), networks = List.of();
    BigDecimal minimum;
    Instant from = NOW.minusSeconds(60), until = NOW.plusSeconds(60);
    Offer.Voucher voucher;
    Offer.Discount discount = new Offer.Discount("FLAT", new BigDecimal("20"), null);
    Offer build() {
        return new Offer(key, provider, merchant, "Test offer", type, mode, voucher, discount, minimum,
                issuers, instruments, networks, null, from, until, usage, stacking, List.of("Synthetic test terms"), availability,
                URI.create("https://www.gyftr.com/swiggy-money"), URI.create("https://evil.example/"), "Untrusted label",
                verification, NOW, NOW, "a".repeat(64));
    }
    static Offer voucher(String face, String price) {
        var example = new OfferExample();
        example.type = "VOUCHER_DISCOUNT"; example.mode = "VOUCHER";
        example.voucher = new Offer.Voucher(new BigDecimal(face), new BigDecimal(price));
        example.discount = new Offer.Discount("PERCENTAGE", new BigDecimal("2.50"), null);
        return example.build();
    }
}
