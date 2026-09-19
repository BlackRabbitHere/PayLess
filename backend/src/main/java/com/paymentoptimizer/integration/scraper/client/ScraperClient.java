package com.paymentoptimizer.integration.scraper.client;

import com.paymentoptimizer.integration.scraper.dto.ScraperRequest;
import com.paymentoptimizer.integration.scraper.dto.ScraperResponse;
import com.paymentoptimizer.integration.scraper.dto.ScraperHealthResponse;
import com.paymentoptimizer.integration.scraper.dto.ScraperProviderStatusDto;
import com.paymentoptimizer.integration.scraper.dto.ScraperErrorDto;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import com.paymentoptimizer.integration.scraper.exception.ScraperException;
import java.util.function.Supplier;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

@Component
public class ScraperClient {
    private final RestClient client;
    private final ObjectMapper json;
    public ScraperClient(@Qualifier("scraperRestClient") RestClient client, ObjectMapper json) {
        this.client = client;
        this.json = json;
    }

    public ScraperHealthResponse health() {
        return request(() -> client.get().uri("/health").retrieve().body(ScraperHealthResponse.class));
    }

    public ScraperProviderStatusDto.Response providers() {
        return request(() -> client.get().uri("/api/v1/providers").retrieve().body(ScraperProviderStatusDto.Response.class));
    }

    public ScraperResponse scrape(ScraperRequest request) {
        return request(() -> client.post().uri("/api/v1/scrape").contentType(MediaType.APPLICATION_JSON)
                .body(request).retrieve().body(ScraperResponse.class));
    }

    private <T> T request(Supplier<T> action) {
        try {
            T response = action.get();
            if (response == null) throw ScraperException.invalidContract();
            return response;
        } catch (ResourceAccessException exception) {
            throw new ScraperException("SCRAPER_UNAVAILABLE", "Scraper is unavailable or the request timed out.", true);
        } catch (RestClientResponseException exception) {
            throw new ScraperException("SCRAPER_HTTP_" + exception.getStatusCode().value(),
                    "Scraper could not complete the request.", exception.getStatusCode().value() == 503
                    || exception.getStatusCode().value() == 429, errors(exception));
        } catch (RestClientException exception) {
            throw ScraperException.invalidContract();
        }
    }

    private List<ScraperErrorDto> errors(RestClientResponseException exception) {
        try {
            var body = json.readTree(exception.getResponseBodyAsByteArray());
            if (body == null || body.path("schemaVersion").asInt() != 1 || !body.path("errors").isArray()) return List.of();
            var errors = json.treeToValue(body.get("errors"), ScraperErrorDto[].class);
            if (java.util.Arrays.stream(errors).anyMatch(e -> e == null || e.code() == null || e.message() == null)) return List.of();
            return List.of(errors);
        } catch (java.io.IOException | IllegalArgumentException ignored) {
            return List.of();
        }
    }
}
