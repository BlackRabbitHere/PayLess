package com.paymentoptimizer;

import static org.assertj.core.api.Assertions.*;
import com.paymentoptimizer.integration.scraper.client.ScraperClient;
import com.paymentoptimizer.integration.scraper.config.ScraperClientConfiguration;
import com.paymentoptimizer.integration.scraper.config.ScraperProperties;
import com.paymentoptimizer.integration.scraper.dto.ScraperHealthResponse;
import com.paymentoptimizer.integration.scraper.exception.ScraperException;
import com.paymentoptimizer.integration.scraper.mapper.ScraperOfferMapper;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.URI;
import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Bean;
import org.springframework.mock.env.MockEnvironment;
import org.springframework.web.client.RestClient;

class ScraperConfigurationTest {
    @Configuration(proxyBeanMethods = false)
    @EnableConfigurationProperties(ScraperProperties.class)
    static class TestConfig {
        @Bean RestClient.Builder restClientBuilder() { return RestClient.builder(); }
    }

    final ApplicationContextRunner runner = new ApplicationContextRunner()
            .withUserConfiguration(TestConfig.class, ScraperClientConfiguration.class)
            .withPropertyValues("scraper.base-url=http://127.0.0.1:8000", "scraper.connect-timeout=5s", "scraper.read-timeout=30s");

    @Test
    void bindsUrlAndTimeoutOverrides() {
        runner.withPropertyValues("scraper.base-url=http://scraper:8000", "scraper.read-timeout=7s").run(context -> {
            assertThat(context).hasNotFailed();
            var properties = context.getBean(ScraperProperties.class);
            assertThat(properties.baseUrl()).isEqualTo(URI.create("http://scraper:8000"));
            assertThat(properties.connectTimeout()).isEqualTo(Duration.ofSeconds(5));
            assertThat(properties.readTimeout()).isEqualTo(Duration.ofSeconds(7));
        });
    }

    @Test
    void rejectsInvalidConfiguration() {
        runner.withPropertyValues("scraper.connect-timeout=0s").run(context -> assertThat(context).hasFailed());
        runner.withPropertyValues("scraper.base-url=file:///tmp/scraper").run(context -> assertThat(context).hasFailed());
    }

    @Test
    void productionRejectsFixturesEvenWithAnExplicitOverride() throws Exception {
        var properties = new ScraperProperties(URI.create("http://localhost:8000"), Duration.ofSeconds(5), Duration.ofSeconds(30), true);
        var environment = new MockEnvironment();
        environment.setActiveProfiles("production");
        var mapper = new ScraperOfferMapper(properties, environment);
        assertThatThrownBy(() -> mapper.health(new ScraperHealthResponse("ok", 1, "fixture")))
                .isInstanceOf(ScraperException.class).hasMessageContaining("Fixture data is disabled");
        var response = new com.fasterxml.jackson.databind.ObjectMapper().findAndRegisterModules().readValue(
                ScraperIntegrationTest.fixture("gyftr_swiggy"),
                com.paymentoptimizer.integration.scraper.dto.ScraperResponse.class);
        assertThatThrownBy(() -> mapper.batch(response)).isInstanceOf(ScraperException.class)
                .hasMessageContaining("Fixture data is disabled");
    }

    @Test
    void readTimeoutIsAppliedToTheActualHttpClient() throws Exception {
        var server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/health", exchange -> {
            try { Thread.sleep(500); } catch (InterruptedException exception) { Thread.currentThread().interrupt(); }
            exchange.close();
        });
        server.start();
        try {
            runner.withPropertyValues("scraper.base-url=http://127.0.0.1:" + server.getAddress().getPort(), "scraper.read-timeout=50ms")
                    .run(context -> {
                        var client = new ScraperClient(context.getBean(RestClient.class), new com.fasterxml.jackson.databind.ObjectMapper());
                        assertThatThrownBy(client::health).isInstanceOf(ScraperException.class)
                                .hasMessageContaining("timed out");
                    });
        } finally { server.stop(0); }
    }
}
