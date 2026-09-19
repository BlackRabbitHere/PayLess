package com.paymentoptimizer.offers.application;

import com.paymentoptimizer.offers.domain.Offer;
import com.paymentoptimizer.offers.domain.OfferBatch;
import com.paymentoptimizer.offers.domain.OfferSource;
import com.paymentoptimizer.query.domain.PurchaseContext;
import com.paymentoptimizer.common.exception.UpstreamServiceException;
import java.util.ArrayList;
import java.util.UUID;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class OfferAcquisitionService {
    private final OfferSource source;
    private final OfferProviderCatalog catalog;
    public OfferAcquisitionService(OfferSource source, OfferProviderCatalog catalog) {
        this.source = source;
        this.catalog = catalog;
    }

    /** Each provider is its own failure boundary. No fixture fallback and no forced live refresh. */
    public List<OfferBatch> acquireAvailable(PurchaseContext context) {
        var batches = new ArrayList<OfferBatch>();
        for (var provider : catalog.providersFor(context.merchant())) {
            try {
                var batch = source.fetch(provider, context.merchant().name(), false);
                batches.add(verified(batch));
            } catch (UpstreamServiceException failure) {
                batches.add(new OfferBatch(UUID.randomUUID(), "UNAVAILABLE", provider, context.merchant().name(), false,
                        List.of(), List.of(), List.of(new OfferBatch.Failure(failure.code(),
                        "Offer acquisition unavailable for " + provider + ".", provider, failure.unavailable()))));
            }
        }
        return List.copyOf(batches);
    }

    public List<Offer> acquire(PurchaseContext context) { return acquire(context, false); }

    public List<Offer> acquire(PurchaseContext context, boolean forceRefresh) {
        return acquireBatch(context, forceRefresh).offers();
    }

    /** Retains diagnostics for the checkpoint; the business entry point returns domain offers. */
    public OfferBatch acquireBatch(PurchaseContext context, boolean forceRefresh) {
        String provider = catalog.providersFor(context.merchant()).getFirst();
        var batch = source.fetch(provider, context.merchant().name(), forceRefresh);
        return verified(batch);
    }

    private OfferBatch verified(OfferBatch batch) {
        return new OfferBatch(batch.requestId(), batch.status(), batch.provider(), batch.merchant(), batch.fixture(),
                batch.offers().stream().filter(o -> "VERIFIED".equals(o.verificationStatus())).toList(),
                batch.warnings(), batch.errors());
    }
}
