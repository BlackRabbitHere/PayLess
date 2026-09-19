package com.paymentoptimizer.redirect.domain;

/** Closed backend-owned destinations. Neither requests nor scraped action URLs can create a target. */
public enum ActionTarget { BUY_SWIGGY_VOUCHER, OPEN_SWIGGY, OPEN_YATRA, OPEN_EASEMYTRIP }
