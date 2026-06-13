package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface RealEstateMarketDataTargetRepository extends JpaRepository<RealEstateMarketDataTarget, Long> {

    @Query("""
            select target
            from RealEstateMarketDataTarget target
            where (:enabled is null or target.enabled = :enabled)
            order by target.targetId asc, target.providerDataset asc
            """)
    List<RealEstateMarketDataTarget> listTargets(@Param("enabled") Boolean enabled, Pageable pageable);

    Optional<RealEstateMarketDataTarget> findByTargetIdAndProviderAndProviderDatasetAndLawdCode(
            String targetId,
            String provider,
            String providerDataset,
            String lawdCode
    );
}
