package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface RealEstateMarketFactStagingRepository extends JpaRepository<RealEstateMarketFactStaging, Long> {

    Optional<RealEstateMarketFactStaging> findByRawItemId(Long rawItemId);

    @Query("""
            select staging
            from RealEstateMarketFactStaging staging,
                 RealEstatePublicDataRawItem rawItem,
                 RealEstatePublicDataImportRun run
            where staging.rawItemId = rawItem.id
              and rawItem.importRunId = run.id
              and (:providerDataset is null or staging.providerDataset = :providerDataset)
              and (:runKey is null or run.runKey = :runKey)
              and (:validationStatus is null or staging.validationStatus = :validationStatus)
            order by staging.asOf asc, staging.providerObjectId asc
            """)
    List<RealEstateMarketFactStaging> searchPromotable(
            @Param("providerDataset") String providerDataset,
            @Param("runKey") String runKey,
            @Param("validationStatus") String validationStatus,
            Pageable pageable
    );
}
