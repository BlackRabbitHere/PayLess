package com.paymentoptimizer.redirect.application;

import com.paymentoptimizer.redirect.domain.ActionTarget;
import java.net.URI;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class RedirectSafetyValidator {
    private record Destination(String provider, URI url) {}
    private static final Map<ActionTarget, Destination> DESTINATIONS = Map.of(
            ActionTarget.BUY_SWIGGY_VOUCHER, new Destination("GYFTR", URI.create("https://www.gyftr.com/swiggy-money")),
            ActionTarget.OPEN_SWIGGY, new Destination("SWIGGY", URI.create("https://www.swiggy.com/")),
            ActionTarget.OPEN_YATRA, new Destination("YATRA", URI.create("https://www.yatra.com/")),
            ActionTarget.OPEN_EASEMYTRIP, new Destination("EASEMYTRIP", URI.create("https://www.easemytrip.com/")));
    public URI validate(ActionTarget target) {
        var destination = DESTINATIONS.get(target);
        if (destination == null || !isAllowed(destination.provider(), destination.url())) {
            throw new IllegalArgumentException("Unapproved action target.");
        }
        return destination.url();
    }
    public boolean isAllowed(String provider, URI url) {
        return url != null && "https".equals(url.getScheme()) && url.getHost() != null
                && url.getUserInfo() == null && url.getPort() == -1 && url.getQuery() == null && url.getFragment() == null
                && DESTINATIONS.values().stream().anyMatch(d -> d.provider().equals(provider) && d.url().equals(url));
    }
}
