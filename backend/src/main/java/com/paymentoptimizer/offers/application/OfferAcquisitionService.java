package com.paymentoptimizer.offers.application;

import com.paymentoptimizer.offers.domain.Offer;
import com.paymentoptimizer.offers.domain.OfferBatch;
import com.paymentoptimizer.offers.domain.OfferSource;
import com.paymentoptimizer.offers.domain.OfferStore;
import com.paymentoptimizer.common.observability.RequestCorrelationFilter;
import org.slf4j.LoggerFactory;
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
    private final OfferStore store;
    public OfferAcquisitionService(OfferSource source, OfferProviderCatalog catalog, OfferStore store) {
        this.source = source; this.catalog = catalog; this.store = store;
    }

    private OfferBatch fetch(String provider, String merchant, boolean refresh, boolean tolerateFailure) {
        long start = System.nanoTime();
        String requestId = RequestCorrelationFilter.currentId();
        OfferBatch batch;
        try {
            batch = source.fetch(provider, merchant, refresh);
        } catch (UpstreamServiceException failure) {
            batch = new OfferBatch(UUID.randomUUID(), "UNAVAILABLE", provider, merchant, false,
                    List.of(), List.of(), List.of(new OfferBatch.Failure(failure.code(),
                    "Offer acquisition unavailable for " + provider + ".", provider, failure.unavailable())));
            record(batch, requestId, start);
            if (tolerateFailure) return batch;
            throw failure;
        }
        record(batch, requestId, start);
        return verified(batch);
    }

    private void record(OfferBatch batch, String requestId, long start) {
        long duration = (System.nanoTime() - start) / 1_000_000;
        store.record(batch, requestId, duration);
        var event = LoggerFactory.getLogger(getClass()).atInfo();
        // HTTP correlation is already serialized from MDC by Spring's JSON formatter.
        if (org.slf4j.MDC.get("requestId") == null) event.addKeyValue("requestId", requestId);
        event.addKeyValue("merchant", batch.merchant()).addKeyValue("providersRequested", List.of(batch.provider()))
                .addKeyValue("scraperDurationMs", duration).addKeyValue("offersReceived", batch.offers().size())
                .addKeyValue("partialFailures", batch.errors().size()).log("offers_acquired");
    }

    /** Each provider is its own failure boundary. No fixture fallback and no forced live refresh. */
    public List<OfferBatch> acquireAvailable(PurchaseContext context) {
        var batches = new ArrayList<OfferBatch>();
        for (var provider : catalog.providersFor(context.merchant())) {
            batches.add(fetch(provider, context.merchant().name(), false, true));
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
        return fetch(provider, context.merchant().name(), forceRefresh, false);
    }

    private OfferBatch verified(OfferBatch batch) {
        return new OfferBatch(batch.requestId(), batch.status(), batch.provider(), batch.merchant(), batch.fixture(),
                batch.offers().stream().filter(o -> "VERIFIED".equals(o.verificationStatus())).toList(),
                batch.warnings(), batch.errors());
    }
}
