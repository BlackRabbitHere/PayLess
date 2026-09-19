package com.paymentoptimizer.travel.dto;

import com.fasterxml.jackson.annotation.JsonAnySetter;
import com.paymentoptimizer.optimization.dto.OptimizeRequest;
import com.paymentoptimizer.optimization.dto.OptimizeRequest.Instrument;
import com.paymentoptimizer.travel.domain.TravelSearch;
import com.paymentoptimizer.wallet.domain.Wallet;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.time.LocalDate;
import java.util.List;

public record TravelRequest(
        @NotBlank @Pattern(regexp = "Delhi|Mumbai|Bengaluru|Hyderabad|Chennai|Kolkata") String origin,
        @NotBlank @Pattern(regexp = "Delhi|Mumbai|Bengaluru|Hyderabad|Chennai|Kolkata") String destination,
        @NotNull @FutureOrPresent LocalDate departureDate, @Min(1) @Max(6) int passengers,
        @Valid @Size(max = 20) List<@NotNull @Valid Instrument> wallet) {
    public TravelRequest { wallet = wallet == null ? List.of() : List.copyOf(wallet); }
    @AssertTrue(message = "Choose different origin and destination cities.")
    public boolean isDifferentCities() { return origin == null || !origin.equals(destination); }
    @JsonAnySetter public void rejectUnknown(String name, Object value) {
        throw new IllegalArgumentException("Only travel search fields and wallet metadata are accepted.");
    }
    public TravelSearch toSearch() { return new TravelSearch(origin, destination, departureDate, passengers); }
    public Wallet toWallet() { return new OptimizeRequest("travel", wallet).toWallet(); }
}
