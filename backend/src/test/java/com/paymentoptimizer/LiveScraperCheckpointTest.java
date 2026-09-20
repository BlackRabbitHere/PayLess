package com.paymentoptimizer;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.paymentoptimizer.integration.scraper.client.ScraperClient;
import com.paymentoptimizer.integration.scraper.dto.ScraperRequest;
import com.paymentoptimizer.offers.dto.OfferAcquisitionResponse;
import com.paymentoptimizer.query.domain.Merchant;
import com.paymentoptimizer.query.domain.PurchaseCategory;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;

@org.junit.jupiter.api.Tag("live-scraper")
@EnabledIfEnvironmentVariable(named = "RUN_LIVE_SCRAPER", matches = "true")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        "scraper.base-url=${SCRAPER_BASE_URL:http://127.0.0.1:8000}", "scraper.allow-fixtures=false",
        "scraper.read-timeout=180s"})
class LiveScraperCheckpointTest {
    @Autowired ScraperClient client;
    @Autowired TestRestTemplate http;
    @Autowired ObjectMapper json;

    @Test
    void genuineGyftrResponseCompletesTheSpringDomainBoundary() throws Exception {
        assertThat(client.health().mode()).isEqualTo("live");
        var providers = client.providers();
        assertThat(providers.providers()).anySatisfy(provider -> {
            assertThat(provider.provider()).isEqualTo("GYFTR");
            assertThat(provider.enabled()).isTrue();
            assertThat(provider.merchants()).contains("SWIGGY");
        });
        var response = http.postForEntity("/api/v1/offers/acquisition-check",
                Map.of("sentence", "I am paying 500 rs on swigy", "forceRefresh", true), OfferAcquisitionResponse.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        var result = response.getBody();
        assertThat(result).isNotNull();
        assertThat(result.context().merchant()).isEqualTo(Merchant.SWIGGY);
        assertThat(result.context().category()).isEqualTo(PurchaseCategory.FOOD_DELIVERY);
        assertThat(result.context().amount()).isEqualByComparingTo("500.00");
        assertThat(result.context().confidence()).isEqualByComparingTo("0.96");
        assertThat(result.acquisition().fixture()).isFalse();
        assertThat(result.acquisition().offers()).isNotEmpty().allSatisfy(offer -> {
            assertThat(offer.provider()).isEqualTo("GYFTR");
            assertThat(offer.merchant()).isEqualTo("SWIGGY");
            assertThat(offer.verificationStatus()).isEqualTo("VERIFIED");
            assertThat(offer.sourceUrl().getHost()).isEqualTo("www.gyftr.com");
            assertThat(offer.voucher().sellingPrice()).isNotNull();
        });

        var cached = client.scrape(new ScraperRequest("GYFTR", "SWIGGY", false));
        assertThat(cached.metadata().fixture()).isFalse();
        assertThat(cached.metadata().cacheHit()).isTrue();
        assertThat(cached.metadata().fetchMethod()).isIn("HTTP", "BROWSER");
        assertThat(cached.offers().getFirst().scrapedAt()).isEqualTo(result.acquisition().offers().getFirst().observedAt());
        var fresh = client.scrape(new ScraperRequest("GYFTR", "SWIGGY", true));
        assertThat(fresh.metadata().cacheHit()).isFalse();
        assertThat(fresh.metadata().fixture()).isFalse();
        assertThat(fresh.offers().getFirst().scrapedAt()).isAfter(cached.offers().getFirst().scrapedAt());

        var output = Path.of("../data/verification/phase2");
        Files.createDirectories(output);
        json.writerWithDefaultPrettyPrinter().writeValue(output.resolve("spring-acquisition.json").toFile(), result);
        json.writerWithDefaultPrettyPrinter().writeValue(output.resolve("scraper-response.json").toFile(), fresh);
        json.writerWithDefaultPrettyPrinter().writeValue(output.resolve("provider-statuses.json").toFile(), client.providers());
    }
}
