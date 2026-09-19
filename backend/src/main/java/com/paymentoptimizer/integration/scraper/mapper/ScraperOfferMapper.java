package com.paymentoptimizer.integration.scraper.mapper;

import com.paymentoptimizer.common.api.DependencyStatus;
import com.paymentoptimizer.integration.scraper.config.ScraperProperties;
import com.paymentoptimizer.integration.scraper.dto.ScraperResponse;
import com.paymentoptimizer.integration.scraper.dto.ScrapedOfferDto;
import com.paymentoptimizer.integration.scraper.dto.ScraperHealthResponse;
import com.paymentoptimizer.integration.scraper.exception.ScraperException;
import com.paymentoptimizer.offers.domain.OfferBatch;
import com.paymentoptimizer.offers.domain.Offer;
import java.util.List;
import java.math.BigDecimal;
import java.net.URI;
import org.springframework.core.env.Environment;
import org.springframework.core.env.Profiles;
import org.springframework.stereotype.Component;

@Component
public class ScraperOfferMapper {
    private final boolean allowFixtures;

    public ScraperOfferMapper(ScraperProperties properties, Environment environment) {
        allowFixtures = properties.allowFixtures() && !environment.acceptsProfiles(Profiles.of("production"));
    }

    public DependencyStatus health(ScraperHealthResponse response) {
        if (response == null || !Integer.valueOf(1).equals(response.schemaVersion())
                || !"ok".equals(response.status()) || !List.of("fixture", "live").contains(response.mode() == null ? "" : response.mode())) {
            throw ScraperException.invalidContract();
        }
        rejectFixture("fixture".equals(response.mode()));
        return new DependencyStatus("UP", response.schemaVersion(), response.mode());
    }

    public OfferBatch batch(ScraperResponse response) {
        if (response == null || !Integer.valueOf(1).equals(response.schemaVersion())
                || response.requestId() == null || response.metadata() == null || response.metadata().fixture() == null
                || response.offers() == null || response.warnings() == null || response.errors() == null
                || blank(response.provider()) || blank(response.merchant())
                || response.startedAt() == null || response.completedAt() == null
                || response.completedAt().isBefore(response.startedAt())
                || !List.of("SUCCESS", "PARTIAL").contains(response.status() == null ? "" : response.status())
                || response.offers().isEmpty()) {
            throw ScraperException.invalidContract();
        }
        rejectFixture(response.metadata().fixture());
        if (response.offers().stream().anyMatch(o -> o == null || !response.provider().equals(o.provider())
                || !response.merchant().equals(o.merchant()))
                || response.warnings().stream().anyMatch(w -> w == null || blank(w.code()) || blank(w.message()))
                || response.errors().stream().anyMatch(e -> e == null || blank(e.code()) || blank(e.message()))) {
            throw ScraperException.invalidContract();
        }
        return new OfferBatch(response.requestId(), response.status(), response.provider(), response.merchant(),
                response.metadata().fixture(), response.offers().stream().map(this::offer).toList(),
                response.warnings().stream().map(w -> new OfferBatch.Notice(w.code(), w.message(), w.externalKey())).toList(),
                response.errors().stream().map(e -> new OfferBatch.Failure(e.code(), e.message(), e.provider(), e.retryable())).toList());
    }

    public Offer offer(ScrapedOfferDto offer) {
        if (offer == null || !Integer.valueOf(1).equals(offer.schemaVersion()) || offer.externalKey() == null
                || offer.title() == null || offer.sourceUrl() == null || offer.scrapedAt() == null
                || offer.discount() == null || offer.eligibleIssuers() == null || offer.eligibleInstrumentTypes() == null
                || offer.terms() == null || offer.verificationStatus() == null
                || blank(offer.externalKey()) || blank(offer.title()) || blank(offer.provider()) || blank(offer.merchant())
                || blank(offer.offerType()) || blank(offer.transactionMode()) || blank(offer.discount().type())
                || blank(offer.stackingPolicy()) || blank(offer.availability())
                || offer.contentHash() == null || !offer.contentHash().matches("[a-f0-9]{64}")
                || !https(offer.sourceUrl()) || (offer.actionUrl() != null && !https(offer.actionUrl()))
                || offer.eligibleIssuers().stream().anyMatch(ScraperOfferMapper::blank)
                || offer.eligibleInstrumentTypes().stream().anyMatch(ScraperOfferMapper::blank)
                || offer.terms().stream().anyMatch(ScraperOfferMapper::blank)
                || !List.of("VERIFIED", "AMBIGUOUS", "INCOMPLETE").contains(offer.verificationStatus())
                || ("VERIFIED".equals(offer.verificationStatus()) && offer.lastVerifiedAt() == null)
                || (offer.validFrom() != null && offer.validUntil() != null && offer.validUntil().isBefore(offer.validFrom()))
                || !money(offer.minimumTransaction()) || !money(offer.discount().maximumDiscount())
                || (offer.voucher() != null && (!money(offer.voucher().faceValue()) || !money(offer.voucher().sellingPrice())))
                || !rate(offer.discount().value())
                || ("PERCENTAGE".equals(offer.discount().type()) && offer.discount().value() != null
                    && offer.discount().value().compareTo(new BigDecimal("100")) > 0)
                || (List.of("FLAT", "CASHBACK").contains(offer.discount().type()) && !money(offer.discount().value()))) {
            throw ScraperException.invalidContract();
        }
        var voucher = offer.voucher() == null ? null
                : new Offer.Voucher(offer.voucher().faceValue(), offer.voucher().sellingPrice());
        var discount = new Offer.Discount(offer.discount().type(), offer.discount().value(), offer.discount().maximumDiscount());
        return new Offer(offer.externalKey(), offer.provider(), offer.merchant(), offer.title(),
                offer.offerType(), offer.transactionMode(), voucher, discount, offer.minimumTransaction(),
                List.copyOf(offer.eligibleIssuers()), List.copyOf(offer.eligibleInstrumentTypes()), List.of(), offer.promoCode(),
                offer.validFrom(), offer.validUntil(), offer.usageLimit(), offer.stackingPolicy(), List.copyOf(offer.terms()),
                offer.availability(), offer.sourceUrl(), offer.actionUrl(), offer.actionLabel(),
                offer.verificationStatus(), offer.lastVerifiedAt(), offer.scrapedAt(), offer.contentHash());
    }

    private static boolean blank(String value) { return value == null || value.isBlank(); }
    private static boolean https(URI value) {
        return value != null && "https".equals(value.getScheme()) && value.getHost() != null && value.getUserInfo() == null;
    }
    private static boolean money(BigDecimal value) {
        return value == null || (value.signum() >= 0 && value.stripTrailingZeros().scale() <= 2
                && value.compareTo(new BigDecimal("10000000000000000")) < 0);
    }
    private static boolean rate(BigDecimal value) {
        return value == null || (value.signum() >= 0 && value.stripTrailingZeros().scale() <= 6 && value.precision() <= 12);
    }

    private void rejectFixture(boolean fixture) {
        if (fixture && !allowFixtures) {
            throw new ScraperException("SCRAPER_FIXTURE_REJECTED", "Fixture data is disabled in this environment.", false);
        }
    }
}
