package com.paymentoptimizer.offers.persistence;

import jakarta.persistence.*;

/** Persistence-only model; reference data is versioned by Flyway. */
@Entity
@Table(name = "merchant_alias")
public class MerchantAliasEntity {
    @Id @Column(length = 100) private String alias;
    @Column(nullable = false, length = 32) private String merchant;
    protected MerchantAliasEntity() {}
}
