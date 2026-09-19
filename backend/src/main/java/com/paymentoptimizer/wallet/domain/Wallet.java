package com.paymentoptimizer.wallet.domain;

import java.util.List;

public record Wallet(List<WalletInstrument> instruments) {
    public Wallet { instruments = List.copyOf(instruments); }
}
