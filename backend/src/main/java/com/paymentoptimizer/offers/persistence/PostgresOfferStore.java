package com.paymentoptimizer.offers.persistence;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.paymentoptimizer.offers.domain.OfferBatch;
import com.paymentoptimizer.offers.domain.OfferStore;
import jakarta.persistence.EntityManager;
import java.util.UUID;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
@Profile("!test")
public class PostgresOfferStore implements OfferStore {
    private final EntityManager entityManager;
    private final ObjectMapper json;
    public PostgresOfferStore(EntityManager entityManager, ObjectMapper json) {
        this.entityManager = entityManager; this.json = json;
    }

    @Override @Transactional
    public void record(OfferBatch batch, String requestId, long durationMs) {
        // Stable lock order prevents deadlocks when concurrent scrapes contain the same offers.
        for (var offer : batch.offers().stream().sorted(java.util.Comparator.comparing(o -> o.externalKey())).toList()) {
            if (!batch.merchant().equals(offer.merchant()) || !batch.provider().equals(offer.provider()))
                throw new IllegalArgumentException("Offer identity does not match acquisition");
            String payload;
            try { payload = json.writeValueAsString(offer); }
            catch (JsonProcessingException error) { throw new IllegalStateException("Cannot serialize domain offer", error); }
            entityManager.createNativeQuery("""
                INSERT INTO offer (source_external_key, merchant, provider, verification_status,
                    last_verified_at, valid_until, observed_at, fixture, payload)
                VALUES (:key, :merchant, :provider, :verification, :verified, :expires, :observed, :fixture, CAST(:payload AS jsonb))
                ON CONFLICT (source_external_key) DO UPDATE SET
                    verification_status = EXCLUDED.verification_status, last_verified_at = EXCLUDED.last_verified_at,
                    valid_until = EXCLUDED.valid_until, observed_at = EXCLUDED.observed_at,
                    fixture = EXCLUDED.fixture, payload = EXCLUDED.payload, updated_at = now()
                WHERE offer.merchant = EXCLUDED.merchant AND offer.provider = EXCLUDED.provider
                    AND (offer.fixture OR NOT EXCLUDED.fixture)
                    AND (offer.observed_at <= EXCLUDED.observed_at OR (offer.fixture AND NOT EXCLUDED.fixture))
                """)
                .setParameter("key", offer.externalKey()).setParameter("merchant", offer.merchant())
                .setParameter("provider", offer.provider()).setParameter("verification", offer.verificationStatus())
                .setParameter("verified", offer.lastVerifiedAt()).setParameter("expires", offer.validUntil())
                .setParameter("observed", offer.observedAt()).setParameter("fixture", batch.fixture())
                .setParameter("payload", payload).executeUpdate();
        }
        entityManager.createNativeQuery("""
            INSERT INTO scraper_run (id, request_id, scraper_request_id, merchant, provider, status,
                fixture, offers_received, partial_failures, duration_ms)
            VALUES (:id, :requestId, :scraperId, :merchant, :provider, :status, :fixture, :offers, :failures, :duration)
            """)
            .setParameter("id", UUID.randomUUID()).setParameter("requestId", requestId)
            .setParameter("scraperId", batch.requestId()).setParameter("merchant", batch.merchant())
            .setParameter("provider", batch.provider()).setParameter("status", batch.status())
            .setParameter("fixture", batch.fixture()).setParameter("offers", batch.offers().size())
            .setParameter("failures", batch.errors().size()).setParameter("duration", durationMs).executeUpdate();
    }
}
