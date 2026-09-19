package com.paymentoptimizer.offers.dto;

import com.paymentoptimizer.offers.domain.OfferBatch;
import com.paymentoptimizer.query.domain.PurchaseContext;

public record OfferAcquisitionResponse(PurchaseContext context, OfferBatch acquisition) {}
