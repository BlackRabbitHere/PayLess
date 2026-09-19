package com.paymentoptimizer.common.api;

import org.springframework.stereotype.Service;

@Service
public class SystemStatusService {
    private final ScraperProbe scraper;
    public SystemStatusService(ScraperProbe scraper) { this.scraper = scraper; }

    public SystemStatus status() { return new SystemStatus("UP", scraper.check()); }
    public record SystemStatus(String backend, DependencyStatus scraper) {}
}
