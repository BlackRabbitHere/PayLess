package com.paymentoptimizer;

import static org.assertj.core.api.Assertions.assertThat;
import com.paymentoptimizer.offers.domain.OfferSource;
import com.paymentoptimizer.integration.scraper.client.ScraperClient;
import com.paymentoptimizer.integration.scraper.dto.ScraperRequest;
import com.paymentoptimizer.integration.scraper.exception.ScraperException;
import com.fasterxml.jackson.databind.ObjectMapper;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Map;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class ScraperIntegrationTest {
    static final AtomicReference<String> body = new AtomicReference<>();
    static final AtomicReference<String> lastRequest = new AtomicReference<>();
    static final AtomicReference<String> lastPath = new AtomicReference<>();
    static final AtomicReference<String> lastMethod = new AtomicReference<>();
    static final AtomicInteger status = new AtomicInteger(200);
    static final AtomicInteger calls = new AtomicInteger();
    static final HttpServer upstream = startServer();
    @Autowired TestRestTemplate http;
    @Autowired OfferSource source;
    @Autowired ScraperClient client;
    @Autowired ObjectMapper json;

    static HttpServer startServer() {
        try {
            var server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            server.createContext("/", exchange -> {
                calls.incrementAndGet();
                lastPath.set(exchange.getRequestURI().getPath());
                lastMethod.set(exchange.getRequestMethod());
                lastRequest.set(new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8));
                byte[] bytes = body.get().getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(status.get(), bytes.length);
                exchange.getResponseBody().write(bytes);
                exchange.close();
            });
            server.start();
            return server;
        } catch (IOException exception) { throw new ExceptionInInitializerError(exception); }
    }

    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        registry.add("scraper.base-url", () -> "http://127.0.0.1:" + upstream.getAddress().getPort());
    }

    @BeforeEach
    void reset() throws IOException {
        status.set(200); calls.set(0); body.set(fixture("gyftr_swiggy"));
    }

    @AfterAll
    static void stop() { upstream.stop(0); }

    static String fixture(String name) throws IOException {
        try (var stream = ScraperIntegrationTest.class.getResourceAsStream("/fixtures/scraper/" + name + ".json")) {
            if (stream == null) throw new IOException("Missing contract fixture " + name);
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    @Test
    void springCallsConfiguredScraperAndMapsHealth() {
        body.set("{\"schemaVersion\":1,\"status\":\"ok\",\"mode\":\"fixture\"}");
        var response = http.getForEntity("/api/v1/system/status", String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).contains("\"backend\":\"UP\"", "\"status\":\"UP\"", "\"mode\":\"fixture\"");
        assertThat(calls.get()).isEqualTo(1);
    }

    @Test
    void optimizationEndpointCompletesTypoQueryWithWalletCostsStepsSourcesAndWarnings() throws Exception {
        var response = http.postForEntity("/api/optimize/query", Map.of("query", "I am spending 500 rs on swigy", "wallet", List.of(
                Map.of("issuer", "HDFC", "productName", "Millennia", "instrumentType", "CREDIT_CARD", "network", "VISA"))), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        var result = json.readTree(response.getBody());
        assertThat(result.at("/context/merchant").asText()).isEqualTo("SWIGGY");
        assertThat(result.at("/bestEffectiveCostRoute/cost/payNow").decimalValue()).isEqualByComparingTo("487.50");
        assertThat(result.at("/bestEffectiveCostRoute/cost/effectiveCost").decimalValue()).isEqualByComparingTo("487.50");
        assertThat(result.at("/bestEffectiveCostRoute/cost/saving").decimalValue()).isEqualByComparingTo("12.50");
        assertThat(result.at("/bestPayNowRoute/cost/payNow").decimalValue()).isEqualByComparingTo("487.50");
        assertThat(result.at("/bestEffectiveCostRoute/steps").size()).isEqualTo(4);
        assertThat(result.at("/bestEffectiveCostRoute/steps/0/actionUrl").asText()).isEqualTo("https://www.gyftr.com/swiggy-money");
        assertThat(result.at("/bestEffectiveCostRoute/sources/0/fixture").asBoolean()).isTrue();
        assertThat(result.at("/bestEffectiveCostRoute/sources/0/contentHash").asText()).hasSize(64);
        assertThat(result.at("/alternatives").size()).isEqualTo(3);
        assertThat(result.at("/warnings").size()).isPositive();
        assertThat(lastRequest.get()).contains("\"forceRefresh\":false");
    }

    @ParameterizedTest
    @CsvSource({"503", "502", "500"})
    void optimizationSurvivesCompleteScraperOutage(int upstreamStatus) throws Exception {
        status.set(upstreamStatus); body.set("{\"detail\":\"private failure\"}");
        var response = http.postForEntity("/api/optimize/query", Map.of("query", "I am spending 500 rs on swigy"), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        var result = json.readTree(response.getBody());
        assertThat(result.at("/bestEffectiveCostRoute/kind").asText()).isEqualTo("DIRECT");
        assertThat(result.at("/bestEffectiveCostRoute/cost/payNow").decimalValue()).isEqualByComparingTo("500.00");
        assertThat(result.at("/bestEffectiveCostRoute/cost/saving").decimalValue()).isEqualByComparingTo("0.00");
        assertThat(response.getBody()).contains("Live offer acquisition unavailable").doesNotContain("private failure");
        assertThat(calls.get()).isEqualTo(1);
    }

    @Test
    void curlCompletesThePhaseThreeHttpCheckpoint() throws Exception {
        var directory = java.nio.file.Path.of("../data/verification/phase3").toAbsolutePath().normalize();
        java.nio.file.Files.createDirectories(directory);
        var request = directory.resolve("request.json");
        java.nio.file.Files.writeString(request, """
                {"query":"I am spending 500 rs on swigy","wallet":[
                  {"issuer":"HDFC","productName":"Millennia","instrumentType":"CREDIT_CARD","network":"VISA"}
                ]}
                """);
        var output = directory.resolve("curl-response.json");
        var error = directory.resolve("curl-stderr.txt");
        var curl = System.getProperty("os.name").toLowerCase(java.util.Locale.ROOT).contains("windows") ? "curl.exe" : "curl";
        var process = new ProcessBuilder(curl, "--silent", "--show-error", "--fail-with-body", "--max-time", "15",
                "--noproxy", "*", "-H", "Content-Type: application/json", "--data-binary", "@" + request,
                "--output", output.toString(), http.getRootUri() + "/api/optimize/query")
                .redirectError(error.toFile()).start();
        if (!process.waitFor(20, java.util.concurrent.TimeUnit.SECONDS)) {
            process.destroyForcibly();
            throw new AssertionError("curl checkpoint timed out");
        }
        assertThat(process.exitValue()).withFailMessage(java.nio.file.Files.readString(error)).isZero();
        var result = json.readTree(output.toFile());
        assertThat(result.at("/bestEffectiveCostRoute/cost/effectiveCost").decimalValue()).isEqualByComparingTo("487.50");
        assertThat(result.at("/bestPayNowRoute/cost/payNow").decimalValue()).isEqualByComparingTo("487.50");
        assertThat(result.at("/alternatives").size()).isEqualTo(3);
        assertThat(result.at("/bestEffectiveCostRoute/steps").size()).isEqualTo(4);
        assertThat(result.at("/sources/0/fixture").asBoolean()).isTrue();
        assertThat(result.at("/warnings").size()).isPositive();
    }

    @Test
    void optimizationRejectsVerifiedButIneligibleOffersAndKeepsDirectRoutes() throws Exception {
        body.set(body.get().replace("\"usageLimit\": null", "\"usageLimit\": \"Once per card.\""));
        var response = http.postForEntity("/api/optimize/query", Map.of("query", "500 on swigy"), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).contains("USAGE_RULE_UNCONFIRMED");
        assertThat(json.readTree(response.getBody()).at("/bestEffectiveCostRoute/kind").asText()).isEqualTo("DIRECT");
    }

    @ParameterizedTest
    @org.junit.jupiter.params.provider.ValueSource(strings = {"cardNumber", "cvv", "pin", "otp", "bankCredentials", "redirectUrl"})
    void optimizationRejectsSensitiveOrRedirectFieldsAtBothRequestLevels(String field) {
        var response = http.postForEntity("/api/optimize/query", Map.of("query", "500 on swigy", field, "not-allowed"), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        var instrument = new java.util.HashMap<String, Object>(Map.of("issuer", "HDFC", "productName", "Millennia",
                "instrumentType", "CREDIT_CARD", "network", "VISA"));
        instrument.put(field, "not-allowed");
        response = http.postForEntity("/api/optimize/query", Map.of("query", "500 on swigy", "wallet", List.of(instrument)), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).doesNotContain("not-allowed");
        assertThat(calls.get()).isZero();
    }

    @ParameterizedTest
    @org.junit.jupiter.params.provider.ValueSource(strings = {"4111111111111111", "4111 1111 1111 1111", "4111-1111-1111-1111"})
    void optimizationRejectsInvalidWalletOrQueryBeforeAcquisition(String product) {
        var response = http.postForEntity("/api/optimize/query", Map.of("query", "500 on swigy", "wallet", List.of(
                Map.of("issuer", "HDFC", "productName", product, "instrumentType", "CREDIT_CARD", "network", "VISA"))), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        response = http.postForEntity("/api/optimize/query", Map.of("query", "500 or 600 on swigy"), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(calls.get()).isZero();
    }

    @Test
    void optimizationIgnoresScrapedActionUrlAndPreservesPartialDiagnostics() {
        body.set(body.get().replace("\"actionUrl\": \"https://www.gyftr.com/swiggy-money\"", "\"actionUrl\": \"https://evil.example/redirect\"")
                .replace("\"SUCCESS\"", "\"PARTIAL\"")
                .replace("\"errors\": []", "\"errors\": [{\"code\":\"READ_TIMEOUT\",\"message\":\"Timed out\",\"provider\":\"GYFTR\",\"retryable\":true}]"));
        var response = http.postForEntity("/api/optimize/query", Map.of("query", "500 on swigy"), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).contains("READ_TIMEOUT", "https://www.gyftr.com/swiggy-money").doesNotContain("evil.example");
    }

    @ParameterizedTest
    @CsvSource({"GYFTR,SWIGGY,gyftr_swiggy", "YATRA,YATRA,yatra_yatra", "EASEMYTRIP,EASEMYTRIP,easemytrip_easemytrip"})
    void mapsEveryFrozenProviderContract(String provider, String merchant, String fixture) throws IOException {
        body.set(fixture(fixture));
        var response = http.postForEntity("/api/v1/optimization/scraper-check",
                Map.of("provider", provider, "merchant", merchant), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).contains("\"observations\"", "\"fixture\":true", "\"provider\":\"" + provider + "\"");
        assertThat(lastRequest.get()).contains("\"forceRefresh\":false");
    }

    @Test
    void decimalStringsNullsAndObservationTimeSurviveTheAdapter() {
        var batch = source.fetch("GYFTR", "SWIGGY");
        var offer = batch.offers().getFirst();
        assertThat(offer.voucher().sellingPrice().toPlainString()).isEqualTo("487.50");
        assertThat(offer.voucher().faceValue().toPlainString()).isEqualTo("500.00");
        assertThat(offer.discount().value().toPlainString()).isEqualTo("2.50");
        assertThat(offer.discount().maximumDiscount()).isNull();
        assertThat(offer.minimumTransaction()).isNull();
        assertThat(offer.eligibleIssuers()).isEmpty();
        assertThat(offer.observedAt()).isEqualTo(Instant.parse("2026-09-18T16:30:00Z"));
        assertThat(batch.warnings().getFirst().code()).isEqualTo("FIXTURE_DATA");
    }

    @Test
    void partialResponseAndUnknownOptionalFieldsArePreserved() {
        body.set(body.get().replace("\"status\": \"SUCCESS\"", "\"status\": \"PARTIAL\"")
                .replace("\"schemaVersion\": 1,", "\"futureOptionalField\": true, \"schemaVersion\": 1,"));
        assertThat(source.fetch("GYFTR", "SWIGGY").status()).isEqualTo("PARTIAL");
    }

    @Test
    void invalidInputNeverCallsScraper() {
        var response = http.postForEntity("/api/v1/optimization/scraper-check",
                Map.of("provider", "GYFTR", "merchant", "YATRA"), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(calls.get()).isZero();
    }

    @ParameterizedTest
    @CsvSource({"503,503", "502,502", "422,502"})
    void upstreamErrorsAreControlledAndNeverRetried(int upstreamStatus, int expectedStatus) {
        status.set(upstreamStatus); body.set("{\"detail\":\"private upstream diagnostic\"}");
        var response = http.postForEntity("/api/v1/optimization/scraper-check",
                Map.of("provider", "GYFTR", "merchant", "SWIGGY"), String.class);
        assertThat(response.getStatusCode().value()).isEqualTo(expectedStatus);
        assertThat(response.getBody()).contains("SCRAPER_HTTP_" + upstreamStatus).doesNotContain("private upstream diagnostic");
        assertThat(calls.get()).isEqualTo(1);
    }

    @Test
    void malformedOrUnsupportedContractDoesNotLookLikeAnEmptySuccess() {
        body.set("{\"schemaVersion\":2}");
        var response = http.postForEntity("/api/v1/optimization/scraper-check",
                Map.of("provider", "GYFTR", "merchant", "SWIGGY"), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_GATEWAY);
        assertThat(response.getBody()).contains("SCRAPER_CONTRACT_INVALID");
    }

    @Test
    void allowsOnlyConfiguredBrowserOrigins() {
        var headers = new HttpHeaders();
        headers.setOrigin("http://localhost:5173");
        headers.setAccessControlRequestMethod(HttpMethod.POST);
        var response = http.exchange("/api/v1/optimization/scraper-check", HttpMethod.OPTIONS, new HttpEntity<>(headers), String.class);
        assertThat(response.getHeaders().getAccessControlAllowOrigin()).isEqualTo("http://localhost:5173");
        headers.setOrigin("https://untrusted.example");
        response = http.exchange("/api/v1/optimization/scraper-check", HttpMethod.OPTIONS, new HttpEntity<>(headers), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
    }

    @ParameterizedTest
    @CsvSource({"swigy,GYFTR,SWIGGY,gyftr_swiggy", "yatra,YATRA,YATRA,yatra_yatra",
            "ease my trip,EASEMYTRIP,EASEMYTRIP,easemytrip_easemytrip"})
    void sentenceTravelsThroughSpringAndOnlyTheRelevantProvider(String name, String provider, String merchant,
            String fixtureName) throws Exception {
        body.set(fixture(fixtureName));
        var response = http.postForEntity("/api/v1/offers/acquisition-check",
                Map.of("sentence", "I am paying 500 rs on " + name, "forceRefresh", true), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        var result = json.readTree(response.getBody());
        assertThat(result.at("/context/merchant").asText()).isEqualTo(merchant);
        assertThat(result.at("/context/amount").decimalValue()).isEqualByComparingTo("500.00");
        assertThat(result.at("/acquisition/offers").size()).isPositive();
        assertThat(result.at("/acquisition/fixture").asBoolean()).isTrue();
        assertThat(json.readTree(lastRequest.get())).isEqualTo(json.readTree(
                "{\"provider\":\"" + provider + "\",\"merchant\":\"" + merchant + "\",\"forceRefresh\":true}"));
        assertThat(lastPath.get()).isEqualTo("/api/v1/scrape");
        assertThat(lastMethod.get()).isEqualTo("POST");
        assertThat(calls.get()).isEqualTo(1);
    }

    @Test
    void unverifiedOffersStayOutOfAcquiredDomainOffers() throws Exception {
        body.set(body.get().replace("\"VERIFIED\"", "\"AMBIGUOUS\"")
                .replace("\"SUCCESS\"", "\"PARTIAL\""));
        var response = http.postForEntity("/api/v1/offers/acquisition-check",
                Map.of("sentence", "500 on swigy"), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        var result = json.readTree(response.getBody());
        assertThat(result.at("/acquisition/offers").size()).isZero();
        assertThat(result.at("/acquisition/status").asText()).isEqualTo("PARTIAL");
        assertThat(result.at("/acquisition/warnings").size()).isPositive();
        assertThat(lastRequest.get()).contains("\"forceRefresh\":false");
    }

    @Test
    void invalidSentenceNeverTriggersAcquisition() {
        var response = http.postForEntity("/api/v1/offers/acquisition-check",
                Map.of("sentence", "500 or 600 on swigy"), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).contains("AMOUNT_AMBIGUOUS");
        assertThat(calls.get()).isZero();
    }

    @ParameterizedTest
    @CsvSource({"422", "503", "502", "500"})
    void decodesBothFrozenErrorEnvelopesWithoutRetries(int httpStatus) {
        status.set(httpStatus);
        String error = "{\"code\":\"FUTURE_PROVIDER_ERROR\",\"message\":\"Controlled diagnostic\",\"provider\":\"GYFTR\",\"retryable\":false}";
        body.set(httpStatus == 422 ? "{\"schemaVersion\":1,\"errors\":[" + error + "]}"
                : body.get().replace("\"errors\": []", "\"errors\": [" + error + "]")
                        .replace("\"SUCCESS\"", "\"FAILED\""));
        assertThatThrownBy(() -> client.scrape(new ScraperRequest("GYFTR", "SWIGGY", false)))
                .isInstanceOfSatisfying(ScraperException.class, failure -> {
                    assertThat(failure.errors()).hasSize(1);
                    assertThat(failure.errors().getFirst().code()).isEqualTo("FUTURE_PROVIDER_ERROR");
                    assertThat(failure.errors().getFirst().retryable()).isFalse();
                });
        assertThat(calls.get()).isEqualTo(1);
    }

    @Test
    void preservesPartialProviderErrors() {
        body.set(body.get().replace("\"SUCCESS\"", "\"PARTIAL\"")
                .replace("\"errors\": []", "\"errors\": [{\"code\":\"READ_TIMEOUT\",\"message\":\"Timed out\",\"provider\":\"GYFTR\",\"retryable\":true}]"));
        var batch = source.fetch("GYFTR", "SWIGGY");
        assertThat(batch.offers()).isNotEmpty();
        assertThat(batch.errors().getFirst().code()).isEqualTo("READ_TIMEOUT");
        assertThat(batch.errors().getFirst().retryable()).isTrue();
    }

    @Test
    void preservesOptionalProviderDiagnostics() {
        body.set("""
                {"schemaVersion":1,"providers":[{"provider":"GYFTR","merchants":["SWIGGY"],
                "browserFallback":true,"liveReady":false,"termsReviewed":false,
                "enabled":true,"httpReady":null,"lastSuccessfulScrape":"2026-09-19T13:26:25+05:30"}]}
                """);
        var provider = client.providers().providers().getFirst();
        assertThat(provider.enabled()).isTrue();
        assertThat(provider.httpReady()).isNull();
        assertThat(provider.lastSuccessfulScrape()).isEqualTo("2026-09-19T13:26:25+05:30");
        assertThat(lastPath.get()).isEqualTo("/api/v1/providers");
    }

    @ParameterizedTest
    @CsvSource(value = {"GYFTR|YATRA", "SWIGGY|YATRA", "487.50|-487.50", "487.50|487.501",
            "https://www.gyftr.com|http://www.gyftr.com"}, delimiter = '|')
    void rejectsMismatchedIdentityAndMalformedCommercialData(String before, String after) {
        body.set(body.get().replace(before, after));
        assertThatThrownBy(() -> source.fetch("GYFTR", "SWIGGY"))
                .isInstanceOf(ScraperException.class).hasMessageContaining("malformed");
    }
}
