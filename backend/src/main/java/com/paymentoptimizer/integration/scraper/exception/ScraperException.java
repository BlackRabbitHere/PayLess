package com.paymentoptimizer.integration.scraper.exception;

import com.paymentoptimizer.common.exception.UpstreamServiceException;
import com.paymentoptimizer.integration.scraper.dto.ScraperErrorDto;
import java.util.List;

public class ScraperException extends UpstreamServiceException {
    private final List<ScraperErrorDto> errors;
    public ScraperException(String code, String message, boolean unavailable) {
        this(code, message, unavailable, List.of());
    }

    public ScraperException(String code, String message, boolean unavailable, List<ScraperErrorDto> errors) {
        super(code, message, unavailable);
        this.errors = List.copyOf(errors);
    }

    public List<ScraperErrorDto> errors() { return errors; }

    public static ScraperException invalidContract() {
        return new ScraperException("SCRAPER_CONTRACT_INVALID", "Scraper returned an unsupported or malformed response.", false);
    }
}
