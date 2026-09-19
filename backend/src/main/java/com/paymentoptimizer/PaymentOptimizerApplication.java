package com.paymentoptimizer;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class PaymentOptimizerApplication {
    public static void main(String[] args) {
        SpringApplication.run(PaymentOptimizerApplication.class, args);
    }
}
