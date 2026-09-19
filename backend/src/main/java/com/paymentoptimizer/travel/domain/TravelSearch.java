package com.paymentoptimizer.travel.domain;

import java.time.LocalDate;

public record TravelSearch(String origin, String destination, LocalDate departureDate, int passengers) {}
