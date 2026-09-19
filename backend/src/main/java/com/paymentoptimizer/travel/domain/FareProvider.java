package com.paymentoptimizer.travel.domain;

import java.util.List;

public interface FareProvider {
    List<FareOption> search(TravelSearch search);
}
