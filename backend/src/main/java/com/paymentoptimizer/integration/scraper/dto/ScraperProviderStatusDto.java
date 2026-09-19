package com.paymentoptimizer.integration.scraper.dto;

import java.util.List;

/** ProviderInfo from the frozen OpenAPI; diagnostic dates are nullable strings there. */
public record ScraperProviderStatusDto(String provider, List<String> merchants,
        boolean browserFallback, boolean liveReady, boolean termsReviewed, Boolean enabled,
        Boolean httpReady, Boolean browserReady, Boolean parserReady, Boolean sourceReachable,
        Boolean liveVerified, String lastSuccessfulScrape, String lastFailure, String lastCheckedAt) {
    public record Response(Integer schemaVersion, List<ScraperProviderStatusDto> providers) {}
}
