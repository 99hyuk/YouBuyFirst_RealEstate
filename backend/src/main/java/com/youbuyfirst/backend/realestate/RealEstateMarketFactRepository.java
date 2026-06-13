package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface RealEstateMarketFactRepository extends JpaRepository<RealEstateMarketFact, Long> {

    Optional<RealEstateMarketFact> findByProviderAndProviderDatasetAndProviderObjectId(
            String provider,
            String providerDataset,
            String providerObjectId
    );

    @Query("""
            select fact
            from RealEstateMarketFact fact
            where (:legalDongCode is null or fact.legalDongCode = :legalDongCode)
              and (:factType is null or fact.factType = :factType)
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> search(
            @Param("legalDongCode") String legalDongCode,
            @Param("factType") String factType,
            Pageable pageable
    );

    @Query("""
            select fact
            from RealEstateMarketFact fact
            where fact.targetId = :targetId
              and (:factType is null or fact.factType = :factType)
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> searchByTargetId(
            @Param("targetId") String targetId,
            @Param("factType") String factType,
            Pageable pageable
    );
}
