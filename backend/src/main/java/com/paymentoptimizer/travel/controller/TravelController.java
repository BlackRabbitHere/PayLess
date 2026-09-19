package com.paymentoptimizer.travel.controller;

import com.paymentoptimizer.travel.application.TravelService;
import com.paymentoptimizer.travel.dto.*;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/travel")
public class TravelController {
    private final TravelService service;
    public TravelController(TravelService service) { this.service = service; }
    @PostMapping("/optimize")
    public TravelResponse optimize(@Valid @RequestBody TravelRequest request) { return service.optimize(request); }
}
