package com.youbuyfirst.backend.indicator;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface RealEstateReactionSnapshotRepository extends JpaRepository<RealEstateReactionSnapshot, Long> {

    Optional<RealEstateReactionSnapshot> findByTargetIdAndWindowStartAndWindowEnd(
            String targetId,
            Instant windowStart,
            Instant windowEnd
    );

    @Query("""
            select snapshot
            from RealEstateReactionSnapshot snapshot
            join fetch snapshot.target target
            where snapshot.targetType = :targetType
              and snapshot.windowStart = :windowStart
              and snapshot.windowEnd = :windowEnd
            order by snapshot.mentionCount desc, snapshot.heatScore desc, target.id asc
            """)
    List<RealEstateReactionSnapshot> findRanking(
            @Param("targetType") String targetType,
            @Param("windowStart") Instant windowStart,
            @Param("windowEnd") Instant windowEnd,
            Pageable pageable
    );

    @Query("""
            select max(snapshot.windowStart)
            from RealEstateReactionSnapshot snapshot
            where snapshot.targetType = :targetType
            """)
    Instant findLatestWindowStart(@Param("targetType") String targetType);

    @Query("""
            select max(snapshot.windowStart)
            from RealEstateReactionSnapshot snapshot
            where snapshot.target.id = :targetId
            """)
    Instant findLatestWindowStartByTargetId(@Param("targetId") String targetId);

    @Query("""
            select max(snapshot.windowStart)
            from RealEstateReactionSnapshot snapshot
            where snapshot.target.id in :targetIds
            """)
    Instant findLatestWindowStartByTargetIds(@Param("targetIds") Collection<String> targetIds);

    @Query("""
            select distinct snapshot
            from RealEstateReactionSnapshot snapshot
            join fetch snapshot.target target
            left join fetch snapshot.issues issue
            where target.id = :targetId
              and snapshot.windowStart = :windowStart
              and snapshot.windowEnd = :windowEnd
            """)
    Optional<RealEstateReactionSnapshot> findTargetSnapshot(
            @Param("targetId") String targetId,
            @Param("windowStart") Instant windowStart,
            @Param("windowEnd") Instant windowEnd
    );

    @Query("""
            select snapshot
            from RealEstateReactionSnapshot snapshot
            where snapshot.target.id = :targetId
              and snapshot.asOf <= :asOf
            order by snapshot.asOf desc, snapshot.windowEnd desc
            """)
    List<RealEstateReactionSnapshot> findLatestForMapLayer(
            @Param("targetId") String targetId,
            @Param("asOf") Instant asOf,
            Pageable pageable
    );
}
