package com.paymentoptimizer.optimization.application;

import com.paymentoptimizer.offers.domain.OfferSource;
import com.paymentoptimizer.optimization.dto.ScraperCheckRequest;
import com.paymentoptimizer.optimization.dto.ScraperCheckResponse;
import java.math.BigDecimal;
import org.springframework.stereotype.Service;

@Service
public class ScraperCheckService {
    private final OfferSource source;
    public ScraperCheckService(OfferSource source) { this.source = source; }

    public ScraperCheckResponse check(ScraperCheckRequest request) {
        var batch = source.fetch(request.provider().name(), request.merchant().name());
        var observations = batch.offers().stream().map(offer -> new ScraperCheckResponse.OfferPreview(
                offer.externalKey(), offer.title(), offer.verificationStatus(),
                decimal(offer.voucher() == null ? null : offer.voucher().faceValue()),
                decimal(offer.voucher() == null ? null : offer.voucher().sellingPrice()),
                decimal(offer.discount().value()), decimal(offer.discount().maximumDiscount()),
                offer.sourceUrl().toString(), offer.observedAt())).toList();
        return new ScraperCheckResponse(batch.requestId(), batch.status(), batch.provider(), batch.merchant(),
                batch.fixture(), observations, batch.warnings().stream().map(w -> w.code()).toList(),
                batch.errors().stream().map(e -> e.code()).toList());
    }

    private static String decimal(BigDecimal value) { return value == null ? null : value.toPlainString(); }
}
