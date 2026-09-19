package com.paymentoptimizer.common.exception;

public class UpstreamServiceException extends RuntimeException {
    private final String code;
    private final boolean unavailable;

    public UpstreamServiceException(String code, String message, boolean unavailable) {
        super(message);
        this.code = code;
        this.unavailable = unavailable;
    }
    public String code() { return code; }
    public boolean unavailable() { return unavailable; }
}
