package com.paymentoptimizer.optimization.controller;

import com.paymentoptimizer.optimization.application.OptimizationService;
import com.paymentoptimizer.optimization.dto.OptimizeRequest;
import com.paymentoptimizer.optimization.dto.OptimizeResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/optimize")
public class OptimizationController {
    private final OptimizationService service;
    public OptimizationController(OptimizationService service) { this.service = service; }
    @PostMapping("/query")
    public OptimizeResponse optimize(@Valid @RequestBody OptimizeRequest request) { return service.optimize(request); }
}
