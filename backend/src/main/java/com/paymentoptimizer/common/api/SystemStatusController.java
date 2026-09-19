package com.paymentoptimizer.common.api;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/system")
public class SystemStatusController {
    private final SystemStatusService service;
    public SystemStatusController(SystemStatusService service) { this.service = service; }

    @GetMapping("/status")
    public SystemStatusService.SystemStatus status() { return service.status(); }
}
