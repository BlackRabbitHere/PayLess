package com.paymentoptimizer.offers.application;

import com.paymentoptimizer.offers.domain.Offer;
import com.paymentoptimizer.offers.domain.OfferBatch;
import com.paymentoptimizer.offers.domain.OfferSource;
import com.paymentoptimizer.query.domain.PurchaseContext;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class OfferAcquisitionService {
    private final OfferSource source;
    public OfferAcquisitionService(OfferSource source) { this.source = source; }

    public List<Offer> acquire(PurchaseContext context) { return acquire(context, false); }

    public List<Offer> acquire(PurchaseContext context, boolean forceRefresh) {
        return acquireBatch(context, forceRefresh).offers();
    }

    /** Retains diagnostics for the checkpoint; the business entry point returns domain offers. */
    public OfferBatch acquireBatch(PurchaseContext context, boolean forceRefresh) {
        String provider = switch (context.merchant()) {
            case SWIGGY -> "GYFTR";
            case YATRA -> "YATRA";
            case EASEMYTRIP -> "EASEMYTRIP";
        };
        var batch = source.fetch(provider, context.merchant().name(), forceRefresh);
        return new OfferBatch(batch.requestId(), batch.status(), batch.provider(), batch.merchant(), batch.fixture(),
                batch.offers().stream().filter(o -> "VERIFIED".equals(o.verificationStatus())).toList(),
                batch.warnings(), batch.errors());
    }
}
