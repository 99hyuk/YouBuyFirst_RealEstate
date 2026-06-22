package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
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
            order by
                case when complex.latitude is null or complex.longitude is null then 1 else 0 end asc,
                case
                    when complex.markerDataStatus = 'ok' then 0
                    when complex.markerDataStatus = 'partial' then 1
                    when complex.markerDataStatus = 'candidate' then 2
                    when complex.markerDataStatus = 'mock' then 3
                    else 4
                end asc,
                case when target.displayName like '(%' then 1 else 0 end asc,
                target.displayName asc
            """)
    List<RealEstateComplex> findVisibleMarkersForTarget(
            @Param("targetId") String targetId,
            Pageable pageable
    );

    @Query("""
            select distinct complex
            from RealEstateComplex complex
            join fetch complex.target target
            left join RealEstateAlias alias
                on alias.targetId = target.id
               and lower(alias.targetType) = 'complex'
               and lower(alias.reviewState) = 'approved'
               and alias.ambiguous = false
            where target.id <> :targetId
              and target.targetType = 'complex'
              and complex.latitude is not null
              and complex.longitude is not null
              and (
                    lower(target.displayName) = :query
                 or lower(target.normalizedName) = :normalizedNameQuery
                 or lower(target.displayName) like concat('%', :query, '%')
                 or lower(target.normalizedName) like concat('%', :normalizedNameQuery, '%')
                 or lower(alias.alias) = :query
                 or lower(alias.normalizedAlias) = :aliasQuery
                 or lower(alias.normalizedAlias) like concat('%', :aliasQuery, '%')
              )
            order by
                case
                    when target.reviewState = 'approved' then 0
                    when target.reviewState = 'candidate' then 1
                    else 2
                end asc,
                case
                    when complex.markerDataStatus = 'ok' then 0
                    when complex.markerDataStatus = 'partial' then 1
                    when complex.markerDataStatus = 'candidate' then 2
                    when complex.markerDataStatus = 'mock' then 3
                    else 4
                end asc,
                case
                    when target.dataStatus = 'ok' then 0
                    when target.dataStatus = 'partial' then 1
                    when target.dataStatus = 'candidate' then 2
                    when target.dataStatus = 'mock' then 3
                    else 4
                end asc,
                target.displayName asc
            """)
    List<RealEstateComplex> findCanonicalMarkersByNameOrAlias(
            @Param("targetId") String targetId,
            @Param("query") String query,
            @Param("normalizedNameQuery") String normalizedNameQuery,
            @Param("aliasQuery") String aliasQuery,
            Pageable pageable
    );

    @Query("""
            select complex.targetId
            from RealEstateComplex complex
            where complex.regionTargetId in :regionTargetIds
            """)
    List<String> findTargetIdsByRegionTargetIds(
            @Param("regionTargetIds") Collection<String> regionTargetIds
    );
}
