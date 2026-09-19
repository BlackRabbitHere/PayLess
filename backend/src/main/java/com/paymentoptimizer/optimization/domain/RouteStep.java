package com.paymentoptimizer.optimization.domain;

import com.paymentoptimizer.redirect.domain.ActionTarget;

public record RouteStep(int number, String instruction, String actionLabel, ActionTarget actionTarget) {}
