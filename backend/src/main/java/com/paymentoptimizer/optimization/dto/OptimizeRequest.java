package com.paymentoptimizer.optimization.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.paymentoptimizer.wallet.domain.Wallet;
import com.paymentoptimizer.wallet.domain.WalletInstrument;
import com.paymentoptimizer.wallet.domain.WalletInstrument.InstrumentType;
import com.paymentoptimizer.wallet.domain.WalletInstrument.Network;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.List;
import java.util.Locale;

public record OptimizeRequest(@JsonAlias("sentence") @NotBlank @Size(max = 1000) String query,
        @Valid @Size(max = 20) List<@NotNull @Valid Instrument> wallet) {
    public OptimizeRequest { wallet = wallet == null ? List.of() : List.copyOf(wallet); }
    @JsonAnySetter public void rejectUnknown(String name, Object value) {
        throw new IllegalArgumentException("Only query and wallet metadata are accepted.");
    }
    public Wallet toWallet() {
        return new Wallet(wallet.stream().map(Instrument::toDomain).distinct().toList());
    }
    public record Instrument(
            @NotBlank @Size(max = 80) @Pattern(regexp = "(?!(?:[^0-9]*[0-9]){5})[\\p{L}\\p{N} .&()/-]+") String issuer,
            @NotBlank @Size(max = 100) @Pattern(regexp = "(?!(?:[^0-9]*[0-9]){5})[\\p{L}\\p{N} .&()/-]+") String productName,
            @NotNull InstrumentType instrumentType, @NotNull Network network) {
        @JsonAnySetter public void rejectUnknown(String name, Object value) {
            throw new IllegalArgumentException("Only wallet metadata is accepted.");
        }
        WalletInstrument toDomain() {
            return new WalletInstrument(issuer.strip().toUpperCase(Locale.ROOT), productName.strip(), instrumentType, network);
        }
    }
}
