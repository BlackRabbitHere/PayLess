package com.paymentoptimizer.offers.persistence;

import jakarta.persistence.*;

/** Persistence-only model; reference data is versioned by Flyway. */
@Entity
@Table(name = "scraper_run")
public class ScraperRunEntity {
    @Id private java.util.UUID id;
    @Column(nullable = false, length = 64) private String requestId;
    @Column(nullable = false) private java.util.UUID scraperRequestId;
    @Column(nullable = false, length = 32) private String merchant;
    @Column(nullable = false, length = 32) private String provider;
    @Column(nullable = false, length = 32) private String status;
    private boolean fixture;
    private int offersReceived;
    private int partialFailures;
    private long durationMs;
    private java.time.Instant completedAt;
    protected ScraperRunEntity() {}
}
