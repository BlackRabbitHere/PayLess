package com.paymentoptimizer.integration.scraper.config;

import java.net.http.HttpClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Configuration(proxyBeanMethods = false)
public class ScraperClientConfiguration {
    @Bean
    RestClient scraperRestClient(RestClient.Builder builder, ScraperProperties properties) {
        var httpClient = HttpClient.newBuilder().connectTimeout(properties.connectTimeout())
                .followRedirects(HttpClient.Redirect.NEVER).build();
        var factory = new JdkClientHttpRequestFactory(httpClient);
        factory.setReadTimeout(properties.readTimeout());
        return builder.baseUrl(properties.baseUrl().toString()).requestFactory(factory).build();
    }
}
