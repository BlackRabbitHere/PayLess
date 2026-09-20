package com.paymentoptimizer;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.paymentoptimizer.offers.domain.*;
import com.paymentoptimizer.offers.persistence.OfferRepository;
import com.paymentoptimizer.integration.scraper.dto.ScraperResponse;
import com.paymentoptimizer.integration.scraper.mapper.ScraperOfferMapper;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;

/** Real PostgreSQL/Flyway, never H2. Enable with -Pdatabase-tests and an isolated DATABASE_URL. */
@Tag("repository")
@SpringBootTest
@ActiveProfiles("local")
class PostgresRepositoryTest {
    @Autowired OfferStore store;
    @Autowired OfferRepository offers;
    @Autowired JdbcTemplate sql;
    @Autowired ObjectMapper json;
    @Autowired ScraperOfferMapper mapper;
    final String requestId = "repository-" + UUID.randomUUID();
    final List<String> keys = new ArrayList<>();

    OfferBatch fixture() throws Exception {
        var batch = mapper.batch(json.readValue(ScraperIntegrationTest.fixture("gyftr_swiggy"), ScraperResponse.class));
        var node = json.valueToTree(batch.offers().getFirst());
        String key = "test-" + UUID.randomUUID(); keys.add(key);
        ((com.fasterxml.jackson.databind.node.ObjectNode) node).put("externalKey", key);
        var offer = json.treeToValue(node, Offer.class);
        return new OfferBatch(batch.requestId(), batch.status(), batch.provider(), batch.merchant(), true,
                List.of(offer), batch.warnings(), batch.errors());
    }
    OfferBatch change(OfferBatch batch, String status, Instant observed, boolean fixture) throws Exception {
        var node = (com.fasterxml.jackson.databind.node.ObjectNode) json.valueToTree(batch.offers().getFirst());
        node.put("verificationStatus", status); node.put("observedAt", observed.toString());
        return new OfferBatch(batch.requestId(), "PARTIAL", batch.provider(), batch.merchant(), fixture,
                List.of(json.treeToValue(node, Offer.class)), List.of(), List.of());
    }
    @AfterEach void cleanOnlyOwnRows() {
        sql.update("DELETE FROM scraper_run WHERE request_id = ?", requestId);
        keys.forEach(key -> sql.update("DELETE FROM offer WHERE source_external_key = ?", key));
    }
    @Test void migrationsSeedReferenceDataAndIndexes() {
        assertThat(sql.queryForObject("SELECT count(*) FROM flyway_schema_history WHERE success", Integer.class)).isEqualTo(2);
        assertThat(sql.queryForObject("SELECT merchant FROM merchant_alias WHERE alias = 'swigy'", String.class)).isEqualTo("SWIGGY");
        assertThat(sql.queryForObject("SELECT merchant FROM provider WHERE code = 'GYFTR'", String.class)).isEqualTo("SWIGGY");
        assertThat(sql.queryForList("SELECT indexname FROM pg_indexes WHERE tablename = 'offer'", String.class))
                .contains("offer_merchant_verification_idx", "offer_valid_until_idx", "offer_source_external_key_key");
    }
    @Test void repeatScrapesUpsertAndRoundTripExactMoneyNullsAndDates() throws Exception {
        var batch = fixture();
        store.record(batch, requestId, 12); store.record(batch, requestId, 13);
        var entity = offers.findBySourceExternalKey(keys.getFirst()).orElseThrow();
        assertThat(json.readValue(entity.getPayload(), Offer.class)).usingRecursiveComparison()
                .withComparatorForType(java.math.BigDecimal::compareTo, java.math.BigDecimal.class)
                .isEqualTo(batch.offers().getFirst());
        assertThat(sql.queryForObject("SELECT count(*) FROM offer WHERE source_external_key = ?", Integer.class, keys.getFirst())).isEqualTo(1);
        assertThat(sql.queryForObject("SELECT count(*) FROM scraper_run WHERE request_id = ?", Integer.class, requestId)).isEqualTo(2);
        assertThat(entity.getPayload()).doesNotContain("cardNumber", "cvv", "bankCredentials");
    }
    @Test void newestObservationWinsAndVerificationDowngradesArePersisted() throws Exception {
        var batch = fixture(); store.record(batch, requestId, 0);
        var newer = change(batch, "AMBIGUOUS", batch.offers().getFirst().observedAt().plusSeconds(10), true);
        store.record(newer, requestId, 0); store.record(batch, requestId, 0);
        assertThat(offers.findBySourceExternalKey(keys.getFirst()).orElseThrow().getVerificationStatus()).isEqualTo("AMBIGUOUS");
    }
    @Test void fixtureCannotOverwriteLiveEvenWithNewerTimestamp() throws Exception {
        var batch = fixture();
        store.record(change(batch, "VERIFIED", batch.offers().getFirst().observedAt(), false), requestId, 0);
        store.record(change(batch, "AMBIGUOUS", batch.offers().getFirst().observedAt().plusSeconds(10), true), requestId, 0);
        assertThat(offers.findBySourceExternalKey(keys.getFirst()).orElseThrow().getVerificationStatus()).isEqualTo("VERIFIED");
        assertThat(sql.queryForObject("SELECT fixture FROM offer WHERE source_external_key = ?", Boolean.class, keys.getFirst())).isFalse();
    }
    @Test void concurrentSameIdentityRemainsOneOfferWithEveryAttemptAudited() throws Exception {
        var batch = fixture();
        try (var executor = Executors.newFixedThreadPool(6)) {
            var futures = new ArrayList<Future<?>>();
            for (int i = 0; i < 12; i++) futures.add(executor.submit(() -> store.record(batch, requestId, 1)));
            for (var future : futures) future.get(20, TimeUnit.SECONDS);
        }
        assertThat(sql.queryForObject("SELECT count(*) FROM offer WHERE source_external_key = ?", Integer.class, keys.getFirst())).isEqualTo(1);
        assertThat(sql.queryForObject("SELECT count(*) FROM scraper_run WHERE request_id = ?", Integer.class, requestId)).isEqualTo(12);
    }
    @Test void failedRunIsRecordedAndWriteErrorsRollbackOfferAndAuditTogether() throws Exception {
        store.record(new OfferBatch(UUID.randomUUID(), "UNAVAILABLE", "GYFTR", "SWIGGY", false,
                List.of(), List.of(), List.of(new OfferBatch.Failure("TIMEOUT", "Unavailable", "GYFTR", true))), requestId, 50);
        assertThat(sql.queryForObject("SELECT partial_failures FROM scraper_run WHERE request_id = ?", Integer.class, requestId)).isEqualTo(1);
        var batch = fixture();
        assertThatThrownBy(() -> store.record(batch, requestId, -1)).isInstanceOf(RuntimeException.class);
        assertThat(offers.findBySourceExternalKey(keys.getFirst())).isEmpty();
        assertThat(sql.queryForObject("SELECT count(*) FROM scraper_run WHERE request_id = ?", Integer.class, requestId)).isEqualTo(1);
    }
}
