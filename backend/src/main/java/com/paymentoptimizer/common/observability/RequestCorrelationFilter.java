package com.paymentoptimizer.common.observability;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestCorrelationFilter extends OncePerRequestFilter {
    public static final String HEADER = "X-Request-ID";
    public static String currentId() {
        String id = MDC.get("requestId");
        return id == null ? UUID.randomUUID().toString() : id;
    }
    @Override protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
            FilterChain chain) throws ServletException, IOException {
        String supplied = request.getHeader(HEADER);
        String id = supplied != null && supplied.matches("[a-zA-Z0-9_-]{1,64}") ? supplied : UUID.randomUUID().toString();
        try (var ignored = MDC.putCloseable("requestId", id)) {
            response.setHeader(HEADER, id);
            chain.doFilter(request, response);
        }
    }
}
