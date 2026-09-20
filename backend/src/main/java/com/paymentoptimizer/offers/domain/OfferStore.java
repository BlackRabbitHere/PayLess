package com.paymentoptimizer.offers.domain;

/** Stores source observations and an acquisition audit atomically. Never receives wallet data. */
public interface OfferStore {
    void record(OfferBatch batch, String requestId, long durationMs);
}
