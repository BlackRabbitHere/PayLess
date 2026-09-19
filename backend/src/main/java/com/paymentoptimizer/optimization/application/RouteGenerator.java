package com.paymentoptimizer.optimization.application;

import com.paymentoptimizer.offers.application.OfferEligibilityService;
import com.paymentoptimizer.offers.domain.*;
import com.paymentoptimizer.optimization.domain.RouteCandidate;
import com.paymentoptimizer.query.domain.PurchaseContext;
import com.paymentoptimizer.wallet.domain.*;
import java.time.Instant;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.springframework.stereotype.Service;

@Service
public class RouteGenerator {
    private final OfferEligibilityService eligibility;
    public RouteGenerator(OfferEligibilityService eligibility) { this.eligibility = eligibility; }
    public record Assessment(String offerKey, String instrumentKey, EligibilityResult result) {}
    public record Generation(List<RouteCandidate> candidates, List<Assessment> eligibility) {
        public Generation { candidates = List.copyOf(candidates); eligibility = List.copyOf(eligibility); }
    }
    public Generation generate(PurchaseContext purchase, Wallet wallet, List<Offer> offers, Instant now) {
        var instruments = new TreeMap<String, WalletInstrument>();
        instruments.put(WalletInstrument.upi().key(), WalletInstrument.upi());
        wallet.instruments().forEach(i -> instruments.put(i.key(), i));
        var candidates = new ArrayList<RouteCandidate>();
        var assessments = new ArrayList<Assessment>();
        var sortedOffers = offers.stream().sorted(Comparator.comparing(Offer::externalKey)).toList();
        for (var instrument : instruments.values()) {
            candidates.add(candidate("DIRECT", instrument, List.of()));
            var direct = new ArrayList<Offer>();
            for (var offer : sortedOffers) {
                var mode = "VOUCHER".equals(offer.transactionMode()) ? "VOUCHER" : instrument.transactionMode();
                var result = eligibility.evaluate(offer, purchase, instrument, mode, List.of(), now);
                assessments.add(new Assessment(offer.externalKey(), instrument.key(), result));
                if (!result.eligible()) continue;
                if ("VOUCHER".equals(mode)) candidates.add(candidate("VOUCHER", instrument, List.of(offer)));
                else direct.add(offer);
            }
            combinations(purchase, instrument, direct, 0, List.of(), now, candidates);
        }
        return new Generation(candidates.stream().distinct().toList(), assessments);
    }

    /** Enumerates singles and every explicitly stackable subset; never combines unknown voucher redemption scopes. */
    private void combinations(PurchaseContext purchase, WalletInstrument instrument, List<Offer> offers, int start,
            List<Offer> applied, Instant now, List<RouteCandidate> result) {
        for (int i = start; i < offers.size(); i++) {
            var offer = offers.get(i);
            if (!eligibility.evaluate(offer, purchase, instrument, instrument.transactionMode(), applied, now).eligible()) continue;
            var next = new ArrayList<>(applied);
            next.add(offer);
            result.add(candidate("DIRECT", instrument, next));
            combinations(purchase, instrument, offers, i + 1, next, now, result);
        }
    }
    private RouteCandidate candidate(String kind, WalletInstrument instrument, List<Offer> offers) {
        String signature = kind + "|" + instrument.key() + "|" + offers.stream().map(Offer::externalKey).toList();
        return new RouteCandidate(UUID.nameUUIDFromBytes(signature.getBytes(StandardCharsets.UTF_8)).toString(), kind, instrument, offers);
    }
}
