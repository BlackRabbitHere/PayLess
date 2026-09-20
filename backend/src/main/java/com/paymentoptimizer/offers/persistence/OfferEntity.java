package com.paymentoptimizer.offers.persistence;

import jakarta.persistence.*;
import java.time.Instant;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "offer")
public class OfferEntity {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(name = "source_external_key", nullable = false, unique = true, length = 512) private String sourceExternalKey;
    @Column(nullable = false, length = 32) private String merchant;
    @Column(nullable = false, length = 32) private String provider;
    @Column(name = "verification_status", nullable = false, length = 32) private String verificationStatus;
    private Instant lastVerifiedAt;
    private Instant validUntil;
    @Column(nullable = false) private Instant observedAt;
    private boolean fixture;
    @JdbcTypeCode(SqlTypes.JSON) @Column(nullable = false, columnDefinition = "jsonb") private String payload;
    private Instant updatedAt;
    protected OfferEntity() {}
    public String getPayload() { return payload; }
    public String getSourceExternalKey() { return sourceExternalKey; }
    public Instant getObservedAt() { return observedAt; }
    public String getVerificationStatus() { return verificationStatus; }
}
