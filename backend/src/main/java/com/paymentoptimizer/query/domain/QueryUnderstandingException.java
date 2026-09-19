package com.paymentoptimizer.query.domain;

public class QueryUnderstandingException extends RuntimeException {
    private final String code;
    public QueryUnderstandingException(String code, String message) {
        super(message);
        this.code = code;
    }
    public String code() { return code; }
}
