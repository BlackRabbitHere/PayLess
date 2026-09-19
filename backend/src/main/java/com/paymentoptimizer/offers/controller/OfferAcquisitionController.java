package com.paymentoptimizer.offers.controller;

import com.paymentoptimizer.offers.application.OfferAcquisitionCheckpoint;
import com.paymentoptimizer.offers.dto.OfferAcquisitionRequest;
import com.paymentoptimizer.offers.dto.OfferAcquisitionResponse;
import jakarta.validation.Valid;
import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/** Explicit integration checkpoint. Live synchronous scraping is not a user search API. */
@RestController
@Profile("!production")
public class OfferAcquisitionController {
    private final OfferAcquisitionCheckpoint checkpoint;
    public OfferAcquisitionController(OfferAcquisitionCheckpoint checkpoint) { this.checkpoint = checkpoint; }

    @PostMapping("/api/v1/offers/acquisition-check")
    public OfferAcquisitionResponse acquire(@Valid @RequestBody OfferAcquisitionRequest request) {
        return checkpoint.acquire(request);
    }
}
