package com.youbuyfirst.backend.realestate;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface RealEstatePublicDataRawItemRepository extends JpaRepository<RealEstatePublicDataRawItem, Long> {

    Optional<RealEstatePublicDataRawItem> findByProviderDatasetAndProviderObjectId(
            String providerDataset,
            String providerObjectId
    );
}
