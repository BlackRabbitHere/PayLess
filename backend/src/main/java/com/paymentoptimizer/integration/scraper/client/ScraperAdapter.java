package com.paymentoptimizer.integration.scraper.client;

import com.paymentoptimizer.common.api.DependencyStatus;
import com.paymentoptimizer.common.api.ScraperProbe;
import com.paymentoptimizer.integration.scraper.mapper.ScraperOfferMapper;
import com.paymentoptimizer.integration.scraper.dto.ScraperRequest;
import com.paymentoptimizer.offers.domain.OfferBatch;
import com.paymentoptimizer.offers.domain.OfferSource;
import org.springframework.stereotype.Component;

@Component
public class ScraperAdapter implements OfferSource, ScraperProbe {
    private final ScraperClient client;
    private final ScraperOfferMapper mapper;

    public ScraperAdapter(ScraperClient client, ScraperOfferMapper mapper) {
        this.client = client;
        this.mapper = mapper;
    }
    @Override
    public DependencyStatus check() { return mapper.health(client.health()); }
    @Override
    public OfferBatch fetch(String provider, String merchant, boolean forceRefresh) {
        var response = client.scrape(new ScraperRequest(provider, merchant, forceRefresh));
        if (!provider.equals(response.provider()) || !merchant.equals(response.merchant())) {
            throw com.paymentoptimizer.integration.scraper.exception.ScraperException.invalidContract();
        }
        return mapper.batch(response);
    }
}
