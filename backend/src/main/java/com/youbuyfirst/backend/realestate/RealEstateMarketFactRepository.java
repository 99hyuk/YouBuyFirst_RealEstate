package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDate;
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
            where (:targetId is null or fact.targetId = :targetId)
              and (:legalDongCode is null or fact.legalDongCode = :legalDongCode)
              and (:factType is null or fact.factType = :factType)
              and (:dealMonth is null or fact.asOf = :dealMonth)
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> search(
            @Param("targetId") String targetId,
            @Param("legalDongCode") String legalDongCode,
            @Param("factType") String factType,
            @Param("dealMonth") LocalDate dealMonth,
            Pageable pageable
    );

    @Query("""
            select fact
            from RealEstateMarketFact fact
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> findLatest(Pageable pageable);

    @Query("""
            select fact
            from RealEstateMarketFact fact
            where fact.legalDongCode = :legalDongCode
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> findLatestByLegalDongCode(
            @Param("legalDongCode") String legalDongCode,
            Pageable pageable
    );

    @Query("""
            select fact
            from RealEstateMarketFact fact
            where fact.factType = :factType
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> findLatestByFactType(
            @Param("factType") String factType,
            Pageable pageable
    );

    @Query("""
            select fact
            from RealEstateMarketFact fact
            where fact.legalDongCode = :legalDongCode
              and fact.factType = :factType
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> findLatestByLegalDongCodeAndFactType(
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

    @Query("""
            select fact
            from RealEstateMarketFact fact
            where fact.targetId = :targetId
              and (:factType is null or fact.factType = :factType)
              and fact.providerDataset in :providerDatasets
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> searchByTargetIdAndProviderDatasetIn(
            @Param("targetId") String targetId,
            @Param("factType") String factType,
            @Param("providerDatasets") List<String> providerDatasets,
            Pageable pageable
    );

    @Query("""
            select fact
            from RealEstateMarketFact fact
            where fact.legalDongCode = :legalDongCode
              and fact.factType = :factType
              and fact.providerDataset in :providerDatasets
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> findLatestByLegalDongCodeAndFactTypeAndProviderDatasetIn(
            @Param("legalDongCode") String legalDongCode,
            @Param("factType") String factType,
            @Param("providerDatasets") List<String> providerDatasets,
            Pageable pageable
    );

    @Query("""
            select fact
            from RealEstateMarketFact fact
            left join RealEstateRegion region on region.targetId = fact.targetId
            where (fact.targetId = :targetId or region.parentRegionId = :targetId)
              and fact.factType = :factType
              and fact.observedAt between :startDate and :endDate
            order by fact.observedAt asc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> findMapLayerFacts(
            @Param("targetId") String targetId,
            @Param("factType") String factType,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate
    );

    @Query("""
            select fact
            from RealEstateMarketFact fact
            where fact.targetId = :targetId
              and fact.factType = :factType
              and fact.observedAt <= :endDate
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> findLatestMapLayerFactByTargetId(
            @Param("targetId") String targetId,
            @Param("factType") String factType,
            @Param("endDate") LocalDate endDate,
            Pageable pageable
    );

    @Query("""
            select fact
            from RealEstateMarketFact fact
            where fact.targetId = :targetId
              and fact.factType = :factType
              and fact.providerDataset in :providerDatasets
              and fact.observedAt <= :endDate
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> findLatestOfficialMapLayerFactsByTargetId(
            @Param("targetId") String targetId,
            @Param("factType") String factType,
            @Param("providerDatasets") List<String> providerDatasets,
            @Param("endDate") LocalDate endDate,
            Pageable pageable
    );

    @Query("""
            select fact
            from RealEstateMarketFact fact
            where fact.legalDongCode in :lookupCodes
              and fact.factType = :factType
              and fact.providerDataset in :providerDatasets
              and fact.observedAt <= :endDate
            order by fact.observedAt desc, fact.providerObjectId asc
            """)
    List<RealEstateMarketFact> findLatestOfficialMapLayerFactsByLegalDongCodeIn(
            @Param("lookupCodes") List<String> lookupCodes,
            @Param("factType") String factType,
            @Param("providerDatasets") List<String> providerDatasets,
            @Param("endDate") LocalDate endDate,
            Pageable pageable
    );

    @Query("""
            select max(fact.observedAt)
            from RealEstateMarketFact fact
            left join RealEstateRegion region on region.targetId = fact.targetId
            where (fact.targetId = :targetId or region.parentRegionId = :targetId)
              and fact.factType = :factType
              and fact.observedAt <= :endDate
            """)
    Optional<LocalDate> findLatestMapLayerObservedAt(
            @Param("targetId") String targetId,
            @Param("factType") String factType,
            @Param("endDate") LocalDate endDate
    );

    @Query("""
            select fact.legalDongCode as legalDongCode, fact.valueJson as valueJson
            from RealEstateMarketFact fact
            order by fact.id asc
            """)
    List<AddressProjection> findAddressProjections(Pageable pageable);

    interface AddressProjection {
        String getLegalDongCode();

        String getValueJson();
    }
}
