package com.paymentoptimizer.optimization.dto;

import com.paymentoptimizer.offers.domain.Offer;
import com.paymentoptimizer.offers.domain.OfferBatch;
import com.paymentoptimizer.optimization.application.RouteGenerator.Assessment;
import com.paymentoptimizer.optimization.domain.CostBreakdown;
import com.paymentoptimizer.query.domain.PurchaseContext;
import com.paymentoptimizer.wallet.domain.WalletInstrument;
import java.net.URI;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record OptimizeResponse(PurchaseContext context, String currency, Route bestEffectiveCostRoute,
        Route bestPayNowRoute, List<Route> alternatives, List<Assessment> eligibility,
        List<Acquisition> sources, List<String> warnings) {
    public record Route(String id, String kind, WalletInstrument paymentInstrument, CostBreakdown cost,
            int verificationConfidence, int complexity, List<Step> steps, List<SourceMetadata> sources, List<String> warnings) {}
    public record Step(int number, String instruction, String actionLabel, URI actionUrl) {}
    public record Acquisition(UUID requestId, String provider, String status, boolean fixture,
            List<OfferBatch.Notice> warnings, List<OfferBatch.Failure> errors) {}
    public record SourceMetadata(String externalKey, String provider, URI sourceUrl, String verificationStatus,
            Instant lastVerifiedAt, Instant observedAt, String contentHash, boolean fixture, List<String> terms) {
        public static SourceMetadata from(Offer offer, boolean fixture) {
            return new SourceMetadata(offer.externalKey(), offer.provider(), offer.sourceUrl(), offer.verificationStatus(),
                    offer.lastVerifiedAt(), offer.observedAt(), offer.contentHash(), fixture, offer.terms());
        }
    }
}
