package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface RealEstateTargetEdgeRepository extends JpaRepository<RealEstateTargetEdge, Long> {

    Optional<RealEstateTargetEdge> findByFromTargetIdAndToTargetIdAndEdgeType(
            String fromTargetId,
            String toTargetId,
            String edgeType
    );

    @Query("""
            select edge
            from RealEstateTargetEdge edge
            join fetch edge.fromTarget fromTarget
            join fetch edge.toTarget toTarget
            where (:targetId is null
                or (:direction = 'out' and edge.fromTargetId = :targetId)
                or (:direction = 'in' and edge.toTargetId = :targetId)
                or (:direction = 'both' and (edge.fromTargetId = :targetId or edge.toTargetId = :targetId)))
              and (:edgeType is null or edge.edgeType = :edgeType)
              and (:reviewState is null or edge.reviewState = :reviewState)
            order by edge.edgeType asc, fromTarget.displayName asc, toTarget.displayName asc
            """)
    List<RealEstateTargetEdge> searchEdges(
            @Param("targetId") String targetId,
            @Param("direction") String direction,
            @Param("edgeType") String edgeType,
            @Param("reviewState") String reviewState,
            Pageable pageable
    );
}
