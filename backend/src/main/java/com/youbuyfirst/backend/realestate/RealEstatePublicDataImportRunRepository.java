package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface RealEstatePublicDataImportRunRepository extends JpaRepository<RealEstatePublicDataImportRun, Long> {

    Optional<RealEstatePublicDataImportRun> findByRunKey(String runKey);

    @Query("""
            select run
            from RealEstatePublicDataImportRun run
            where (:providerDataset is null or run.providerDataset = :providerDataset)
              and (:status is null or run.status = :status)
            order by run.startedAt desc, run.runKey asc
            """)
    List<RealEstatePublicDataImportRun> search(
            @Param("providerDataset") String providerDataset,
            @Param("status") String status,
            Pageable pageable
    );

    @Query("""
            select run
            from RealEstatePublicDataImportRun run
            where run.runKey in :runKeys
              and (:providerDataset is null or run.providerDataset = :providerDataset)
              and (:status is null or run.status = :status)
            order by run.runKey asc
            """)
    List<RealEstatePublicDataImportRun> searchByRunKeys(
            @Param("runKeys") List<String> runKeys,
            @Param("providerDataset") String providerDataset,
            @Param("status") String status
    );
}
