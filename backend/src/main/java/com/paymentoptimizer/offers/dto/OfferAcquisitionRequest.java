package com.paymentoptimizer.offers.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record OfferAcquisitionRequest(@NotBlank @Size(max = 1000) String sentence, boolean forceRefresh) {}
