package com.paymentoptimizer.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration(proxyBeanMethods = false)
public class WebConfiguration implements WebMvcConfigurer {
    private final CorsProperties properties;
    public WebConfiguration(CorsProperties properties) { this.properties = properties; }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**").allowedOrigins(properties.allowedOrigins().toArray(String[]::new))
                .allowedMethods("GET", "POST", "OPTIONS").allowedHeaders("Content-Type", "Accept", "X-Request-ID").exposedHeaders("X-Request-ID")
                .maxAge(3600);
    }
}
