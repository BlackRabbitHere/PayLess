package com.paymentoptimizer.offers.persistence;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface OfferRepository extends JpaRepository<OfferEntity, Long> {
    Optional<OfferEntity> findBySourceExternalKey(String sourceExternalKey);
}
