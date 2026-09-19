package com.paymentoptimizer;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;
import static com.paymentoptimizer.OfferEligibilityTest.*;
import com.paymentoptimizer.common.exception.UpstreamServiceException;
import com.paymentoptimizer.offers.application.*;
import com.paymentoptimizer.offers.domain.*;
import com.paymentoptimizer.optimization.application.*;
import com.paymentoptimizer.optimization.domain.RouteCandidate;
import com.paymentoptimizer.redirect.application.RedirectSafetyValidator;
import com.paymentoptimizer.redirect.domain.ActionTarget;
import java.net.URI;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

class RedirectAndResilienceTest {
    final RedirectSafetyValidator redirects = new RedirectSafetyValidator();
    @ParameterizedTest @ValueSource(strings = {
            "http://www.gyftr.com/swiggy-money", "https://www.gyftr.com.evil.test/swiggy-money",
            "https://www.gyftr.com@evil.test/swiggy-money", "https://evil.test@www.gyftr.com/swiggy-money",
            "https://www.gyftr.com:444/swiggy-money", "https://www.gyftr.com/swiggy-money?next=https://evil.test",
            "https://www.gyftr.com/swiggy-money#evil", "//www.gyftr.com/swiggy-money",
            "javascript:alert(1)", "https://www.gyftr.com/redirect", "https://www.gyftr.com/%2e%2e/redirect"
    })
    void rejectsAnythingExceptBackendOwnedExactDestinations(String url) {
        assertThat(redirects.isAllowed("GYFTR", URI.create(url))).isFalse();
    }
    @Test void bindsApprovedDomainsToTheirProviderAndBuildsActionsWithoutScrapedUrls() {
        assertThat(redirects.isAllowed("YATRA", URI.create("https://www.gyftr.com/swiggy-money"))).isFalse();
        assertThat(redirects.validate(ActionTarget.BUY_SWIGGY_VOUCHER)).isEqualTo(URI.create("https://www.gyftr.com/swiggy-money"));
        var route = new CostCalculator().calculate(PURCHASE,
                new RouteCandidate("v", "VOUCHER", CARD, List.of(OfferExample.voucher("200", "190"))));
        var steps = new RouteStepBuilder().build(PURCHASE, route);
        assertThat(steps).hasSize(4);
        assertThat(steps.getLast().instruction()).contains("300.00");
        assertThat(steps.stream().filter(s -> s.actionTarget() != null).map(s -> redirects.validate(s.actionTarget()).getHost()))
                .containsExactly("www.gyftr.com", "www.swiggy.com");
    }
    @Test void isolatesEachProviderFailureAndPreservesSuccessfulAndPartialBatches() {
        var source = mock(OfferSource.class);
        var catalog = mock(OfferProviderCatalog.class);
        when(catalog.providersFor(PURCHASE.merchant())).thenReturn(List.of("YATRA", "GYFTR", "EASEMYTRIP"));
        when(source.fetch("YATRA", "SWIGGY", false)).thenThrow(new UpstreamServiceException("TIMEOUT", "private details", true));
        for (String provider : List.of("GYFTR", "EASEMYTRIP")) {
            when(source.fetch(provider, "SWIGGY", false)).thenReturn(new OfferBatch(UUID.randomUUID(), "PARTIAL", provider, "SWIGGY", false,
                    List.of(new OfferExample().build()), List.of(), List.of(new OfferBatch.Failure("PARTIAL_RESULT", "test", provider, true))));
        }
        var results = new OfferAcquisitionService(source, catalog).acquireAvailable(PURCHASE);
        assertThat(results).hasSize(3);
        assertThat(results.getFirst().status()).isEqualTo("UNAVAILABLE");
        assertThat(results.getFirst().errors().getFirst().message()).doesNotContain("private details");
        assertThat(results.get(1).offers()).hasSize(1);
        assertThat(results.get(2).offers()).hasSize(1);
        assertThat(results.get(2).errors()).hasSize(1);
        verify(source).fetch("EASEMYTRIP", "SWIGGY", false);
    }
}
