package com.paymentoptimizer.integration.scraper.config;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.NotNull;
import java.net.URI;
import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties("scraper")
public record ScraperProperties(@NotNull URI baseUrl, @NotNull Duration connectTimeout,
                                @NotNull Duration readTimeout, boolean allowFixtures) {
    @AssertTrue(message = "scraper URL must be absolute HTTP(S), without credentials, query or fragment")
    public boolean isValidBaseUrl() {
        return baseUrl != null && ("http".equals(baseUrl.getScheme()) || "https".equals(baseUrl.getScheme()))
                && baseUrl.getHost() != null && baseUrl.getUserInfo() == null
                && baseUrl.getQuery() == null && baseUrl.getFragment() == null;
    }

    @AssertTrue(message = "scraper timeouts must be positive and at most 10 minutes")
    public boolean isValidTimeouts() {
        return validTimeout(connectTimeout) && validTimeout(readTimeout);
    }

    private static boolean validTimeout(Duration value) {
        return value != null && value.toMillis() > 0 && value.compareTo(Duration.ofMinutes(10)) <= 0;
    }
}
