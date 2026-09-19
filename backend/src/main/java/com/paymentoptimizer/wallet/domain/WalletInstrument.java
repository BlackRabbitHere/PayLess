package com.paymentoptimizer.wallet.domain;

import java.util.Objects;

/** Metadata only. No payment credentials or account identifiers belong in this model. */
public record WalletInstrument(String issuer, String productName, InstrumentType instrumentType, Network network) {
    public WalletInstrument {
        Objects.requireNonNull(issuer);
        Objects.requireNonNull(productName);
        Objects.requireNonNull(instrumentType);
        Objects.requireNonNull(network);
    }
    public enum InstrumentType { UPI, CREDIT_CARD, DEBIT_CARD }
    public enum Network { NONE, UNKNOWN, VISA, MASTERCARD, RUPAY, AMEX, DINERS }
    public static WalletInstrument upi() {
        return new WalletInstrument("UPI", "UPI", InstrumentType.UPI, Network.NONE);
    }
    public String key() { return issuer + "/" + productName + "/" + instrumentType + "/" + network; }
    public String transactionMode() { return instrumentType == InstrumentType.UPI ? "UPI" : "CARD"; }
}
