package com.paymentoptimizer.optimization.controller;

import com.paymentoptimizer.optimization.application.ScraperCheckService;
import com.paymentoptimizer.optimization.dto.ScraperCheckRequest;
import com.paymentoptimizer.optimization.dto.ScraperCheckResponse;
import jakarta.validation.Valid;
import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Development contract probe, never the optimization/search path. */
@Profile("!production")
@RestController
@RequestMapping("/api/v1/optimization")
public class ScraperCheckController {
    private final ScraperCheckService service;
    public ScraperCheckController(ScraperCheckService service) { this.service = service; }

    @PostMapping("/scraper-check")
    public ScraperCheckResponse check(@Valid @RequestBody ScraperCheckRequest request) {
        return service.check(request);
    }
}
