package com.paymentoptimizer.offers.application;

import com.paymentoptimizer.offers.dto.OfferAcquisitionRequest;
import com.paymentoptimizer.offers.dto.OfferAcquisitionResponse;
import com.paymentoptimizer.query.application.QueryUnderstandingService;
import org.springframework.stereotype.Service;

@Service
public class OfferAcquisitionCheckpoint {
    private final QueryUnderstandingService queries;
    private final OfferAcquisitionService offers;

    public OfferAcquisitionCheckpoint(QueryUnderstandingService queries, OfferAcquisitionService offers) {
        this.queries = queries;
        this.offers = offers;
    }

    public OfferAcquisitionResponse acquire(OfferAcquisitionRequest request) {
        var context = queries.understand(request.sentence());
        return new OfferAcquisitionResponse(context, offers.acquireBatch(context, request.forceRefresh()));
    }
}
