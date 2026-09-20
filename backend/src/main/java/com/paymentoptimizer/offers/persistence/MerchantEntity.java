package com.paymentoptimizer.offers.persistence;

import jakarta.persistence.*;

/** Persistence-only model; reference data is versioned by Flyway. */
@Entity
@Table(name = "merchant")
public class MerchantEntity {
    @Id @Column(length = 32) private String code;
    @Column(nullable = false, length = 100) private String displayName;
    @Column(nullable = false, length = 32) private String category;
    protected MerchantEntity() {}
}
