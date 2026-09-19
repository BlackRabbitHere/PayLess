package com.paymentoptimizer.optimization.domain;

import com.paymentoptimizer.offers.domain.Offer;
import com.paymentoptimizer.wallet.domain.WalletInstrument;
import java.util.List;

public record RouteCandidate(String id, String kind, WalletInstrument paymentInstrument, List<Offer> offers) {
    public RouteCandidate { offers = List.copyOf(offers); }
    public boolean voucher() { return "VOUCHER".equals(kind); }
    public int complexity() { return (voucher() ? 4 : 2) + offers.size(); }
    public int verificationConfidence() {
        return offers.stream().allMatch(o -> "VERIFIED".equals(o.verificationStatus())) ? 100 : 0;
    }
}
