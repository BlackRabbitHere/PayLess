package com.paymentoptimizer;

import static org.assertj.core.api.Assertions.*;
import com.paymentoptimizer.common.observability.RequestCorrelationFilter;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.slf4j.MDC;

class RequestCorrelationTest {
    @Test void propagatesValidIdsAndCleansThreadContextEvenOnFailure() throws Exception {
        var filter = new RequestCorrelationFilter();
        var request = new MockHttpServletRequest(); request.addHeader("X-Request-ID", "browser-123");
        var response = new MockHttpServletResponse();
        assertThatThrownBy(() -> filter.doFilter(request, response, (req, res) -> {
            assertThat(MDC.get("requestId")).isEqualTo("browser-123");
            throw new java.io.IOException("test");
        })).isInstanceOf(java.io.IOException.class);
        assertThat(response.getHeader("X-Request-ID")).isEqualTo("browser-123");
        assertThat(MDC.get("requestId")).isNull();
    }
    @Test void replacesInvalidAndOversizedIds() throws Exception {
        for (String value : new String[] {"bad id", "x".repeat(65), "<script>", ""}) {
            var request = new MockHttpServletRequest(); request.addHeader("X-Request-ID", value);
            var response = new MockHttpServletResponse();
            new RequestCorrelationFilter().doFilter(request, response, (req, res) -> {});
            assertThat(response.getHeader("X-Request-ID")).matches("[a-f0-9-]{36}");
        }
    }
}
