package com.paymentoptimizer.common.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(com.paymentoptimizer.query.domain.QueryUnderstandingException.class)
    ProblemDetail invalidQuery(com.paymentoptimizer.query.domain.QueryUnderstandingException exception) {
        var problem = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, exception.getMessage());
        problem.setTitle("Purchase query needs clarification");
        problem.setProperty("code", exception.code());
        return problem;
    }
    @ExceptionHandler(UpstreamServiceException.class)
    ProblemDetail upstream(UpstreamServiceException exception) {
        var problem = ProblemDetail.forStatusAndDetail(exception.unavailable()
                ? HttpStatus.SERVICE_UNAVAILABLE : HttpStatus.BAD_GATEWAY, exception.getMessage());
        problem.setTitle("Scraper request failed");
        problem.setProperty("code", exception.code());
        return problem;
    }

    @ExceptionHandler({MethodArgumentNotValidException.class, HttpMessageNotReadableException.class})
    ProblemDetail invalidRequest(Exception exception) {
        var problem = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST,
                "Provide a valid request with all required fields.");
        problem.setTitle("Invalid request");
        problem.setProperty("code", "INVALID_REQUEST");
        return problem;
    }
}
