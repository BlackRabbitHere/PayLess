package com.paymentoptimizer.offers.domain;

/** External source port; implementations belong to integration, not the domain. */
public interface OfferSource {
    OfferBatch fetch(String provider, String merchant, boolean forceRefresh);

    default OfferBatch fetch(String provider, String merchant) { return fetch(provider, merchant, false); }
}
