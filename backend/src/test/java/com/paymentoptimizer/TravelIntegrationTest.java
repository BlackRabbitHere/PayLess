package com.paymentoptimizer;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.paymentoptimizer.common.exception.UpstreamServiceException;
import com.paymentoptimizer.offers.domain.*;
import com.paymentoptimizer.integration.scraper.client.ScraperAdapter;
import com.paymentoptimizer.optimization.application.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class TravelIntegrationTest {
    @org.springframework.test.context.bean.override.mockito.MockitoBean
    com.paymentoptimizer.offers.domain.OfferStore store;
    @Autowired TestRestTemplate http;
    @Autowired ObjectMapper json;
    @MockitoBean ScraperAdapter source;
    @MockitoSpyBean RouteGenerator generator;
    @MockitoSpyBean CostCalculator calculator;
    @MockitoSpyBean PaymentRouteOptimizer optimizer;

    @BeforeEach void offers() {
        when(source.fetch(anyString(), anyString(), eq(false))).thenAnswer(call -> {
            String provider = call.getArgument(0);
            var offer = new OfferExample();
            offer.provider = provider; offer.merchant = provider; offer.key = provider + "-card";
            offer.from = null; offer.until = null; offer.issuers = List.of("HDFC");
            offer.discount = new Offer.Discount("FLAT", new BigDecimal("500"), null);
            return new OfferBatch(UUID.randomUUID(), "SUCCESS", provider, provider, true,
                    List.of(offer.build()), List.of(), List.of());
        });
    }
    Map<String, Object> request(int passengers, boolean card) {
        return new HashMap<>(Map.of("origin", "Delhi", "destination", "Mumbai", "departureDate", LocalDate.now().plusDays(10).toString(),
                "passengers", passengers, "wallet", card ? List.of(Map.of("issuer", "HDFC", "productName", "Millennia",
                        "instrumentType", "CREDIT_CARD", "network", "VISA")) : List.of()));
    }
    JsonNode optimize(Map<String, Object> request) throws Exception {
        var response = http.postForEntity("/api/travel/optimize", request, String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        return json.readTree(response.getBody());
    }
    @Test void ranksFaresWithWalletThroughExistingDomainServicesAndMapsEveryRouteToItsFare() throws Exception {
        var result = optimize(request(2, true));
        assertThat(result.path("fares")).hasSize(2);
        assertThat(result.at("/fares/0/totalAmount").decimalValue()).isEqualByComparingTo("11300");
        var best = result.at("/optimization/bestEffectiveCostRoute");
        assertThat(best.at("/cost/payNow").decimalValue()).isEqualByComparingTo("10418");
        assertThat(best.at("/cost/saving").decimalValue()).isEqualByComparingTo("500");
        assertThat(result.path("routeFareIds").path(best.path("id").asText()).asText()).isEqualTo("demo-easemytrip");
        assertThat(best.at("/steps/0/actionUrl").asText()).isEqualTo("https://www.easemytrip.com/");
        assertThat(result.at("/fares/0/demo").asBoolean()).isTrue();
        verify(generator, times(2)).generate(any(), any(), anyList(), any());
        verify(calculator, atLeast(4)).calculate(any(), any());
        verify(optimizer).rank(anyList());
        verify(source).fetch("YATRA", "YATRA", false);
        verify(source).fetch("EASEMYTRIP", "EASEMYTRIP", false);
        var ids = new HashSet<String>();
        ids.add(best.path("id").asText());
        result.at("/optimization/alternatives").forEach(route -> assertThat(ids.add(route.path("id").asText())).isTrue());
        var noCard = optimize(request(2, false));
        assertThat(noCard.at("/optimization/bestEffectiveCostRoute/cost/payNow").decimalValue()).isEqualByComparingTo("10918");
    }
    @Test void isolatesProviderFailuresAndStillReturnsDirectRoutesWhenAllOffersFail() throws Exception {
        when(source.fetch(eq("YATRA"), anyString(), eq(false))).thenThrow(new UpstreamServiceException("TIMEOUT", "unavailable", true));
        var partial = optimize(request(1, true));
        assertThat(partial.at("/optimization/bestEffectiveCostRoute/cost/payNow").decimalValue()).isEqualByComparingTo("4959");
        assertThat(partial.at("/optimization/sources/0/status").asText()).isEqualTo("UNAVAILABLE");
        when(source.fetch(eq("EASEMYTRIP"), anyString(), eq(false))).thenThrow(new UpstreamServiceException("TIMEOUT", "unavailable", true));
        var unavailable = optimize(request(1, true));
        assertThat(unavailable.at("/optimization/bestEffectiveCostRoute/cost/payNow").decimalValue()).isEqualByComparingTo("5459");
        assertThat(unavailable.at("/optimization/warnings").toString()).contains("Live offer acquisition unavailable");
    }
    @Test void emptyFareResultsDoNotAcquireOffers() throws Exception {
        var request = request(1, false); request.put("destination", "Chennai");
        var result = optimize(request);
        assertThat(result.path("fares")).isEmpty();
        assertThat(result.path("optimization").isNull()).isTrue();
        verifyNoInteractions(source);
    }
    @Test void validatesCitiesDatesPassengersAndWalletMetadataAtTheHttpBoundary() {
        for (var invalid : List.of(Map.entry("destination", (Object) "Delhi"), Map.entry("departureDate", (Object) "2020-01-01"),
                Map.entry("passengers", (Object) 0), Map.entry("passengers", (Object) 7), Map.entry("origin", (Object) "Unknown"),
                Map.entry("cardNumber", (Object) "1234"))) {
            var request = request(1, true); request.put(invalid.getKey(), invalid.getValue());
            assertThat(http.postForEntity("/api/travel/optimize", request, String.class).getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        }
        var request = request(1, true); request.put("wallet", List.of(Map.of("issuer", "HDFC", "productName", "Millennia", "cvv", "123")));
        assertThat(http.postForEntity("/api/travel/optimize", request, String.class).getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        verifyNoInteractions(source);
    }
}
