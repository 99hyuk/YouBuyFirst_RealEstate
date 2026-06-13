package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface RealEstateComplexRepository extends JpaRepository<RealEstateComplex, String> {

    @Query("""
            select distinct complex
            from RealEstateComplex complex
            join fetch complex.target target
            left join RealEstateTargetEdge edge
                on edge.toTargetId = complex.targetId
               and edge.fromTargetId = :targetId
               and (edge.reviewState = 'approved' or edge.source = 'seed:complex-map-marker')
               and edge.edgeType in ('contains', 'nearby', 'same_living_area')
            where complex.targetId = :targetId
               or complex.regionTargetId = :targetId
               or edge.id is not null
            order by target.displayName asc
            """)
    List<RealEstateComplex> findVisibleMarkersForTarget(
            @Param("targetId") String targetId,
            Pageable pageable
    );
}
