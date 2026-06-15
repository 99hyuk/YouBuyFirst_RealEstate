package com.youbuyfirst.backend.realestate;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface RealEstateContentTargetLinkRepository
        extends JpaRepository<RealEstateContentTargetLink, RealEstateContentTargetLinkId> {

    @Query("""
            select link
            from RealEstateContentTargetLink link
            join fetch link.contentItem item
            where link.targetId = :targetId
              and link.reviewState = 'approved'
              and (:contentType is null or item.contentType = :contentType)
            order by item.publishedAt desc nulls last, item.ingestedAt desc, item.id asc
            """)
    List<RealEstateContentTargetLink> findApprovedByTarget(
            @Param("targetId") String targetId,
            @Param("contentType") String contentType,
            Pageable pageable
    );

    @Query("""
            select link
            from RealEstateContentTargetLink link
            join fetch link.contentItem item
            where link.targetId = :targetId
              and (:contentType is null or item.contentType = :contentType)
              and (:reviewState is null or link.reviewState = :reviewState)
              and (:linkType is null or link.linkType = :linkType)
            order by item.publishedAt desc nulls last, item.ingestedAt desc, item.id asc
            """)
    List<RealEstateContentTargetLink> findInternalByTarget(
            @Param("targetId") String targetId,
            @Param("contentType") String contentType,
            @Param("reviewState") String reviewState,
            @Param("linkType") String linkType,
            Pageable pageable
    );
}
