package com.paymentoptimizer.integration.scraper.dto;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record ScraperResponse(Integer schemaVersion, UUID requestId, String status, String provider,
        String merchant, Instant startedAt, Instant completedAt, List<ScrapedOfferDto> offers,
        List<Warning> warnings, List<ScraperErrorDto> errors, Metadata metadata) {
    public record Warning(String code, String message, String externalKey) {}
    public record Metadata(boolean cacheHit, String fetchMethod, int offersFound, int offersExcluded, Boolean fixture) {}
}
