package com.paymentoptimizer.integration.scraper.dto;

public record ScraperRequest(String provider, String merchant, boolean forceRefresh) {}
