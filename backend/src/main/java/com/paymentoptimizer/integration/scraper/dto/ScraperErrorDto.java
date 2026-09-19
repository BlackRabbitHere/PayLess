package com.paymentoptimizer.integration.scraper.dto;

/** Error codes stay strings so future provider diagnostics remain readable. */
public record ScraperErrorDto(String code, String message, String provider, boolean retryable) {}
