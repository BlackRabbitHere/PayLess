package com.paymentoptimizer.common.api;

/** Port implemented by the external adapter; no external DTO crosses this boundary. */
public interface ScraperProbe {
    DependencyStatus check();
}
