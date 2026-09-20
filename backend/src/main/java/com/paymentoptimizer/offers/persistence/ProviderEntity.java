package com.paymentoptimizer.offers.persistence;

import jakarta.persistence.*;

/** Persistence-only model; reference data is versioned by Flyway. */
@Entity
@Table(name = "provider")
public class ProviderEntity {
    @Id @Column(length = 32) private String code;
    @Column(nullable = false, length = 100) private String displayName;
    @Column(nullable = false, length = 32) private String merchant;
    protected ProviderEntity() {}
}
