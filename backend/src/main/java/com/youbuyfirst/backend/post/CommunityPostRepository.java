package com.youbuyfirst.backend.post;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

public interface CommunityPostRepository extends JpaRepository<CommunityPost, Long> {

    boolean existsBySourceAndExternalId(String source, String externalId);

    Optional<CommunityPost> findBySourceAndExternalId(String source, String externalId);

    List<CommunityPost> findByOrderByPublishedAtDesc(Pageable pageable);

    List<CommunityPost> findBySourceOrderByPublishedAtDesc(String source, Pageable pageable);

    Optional<CommunityPost> findFirstBySourceAndBoardIdOrderByPublishedAtDescCrawledAtDesc(String source, String boardId);

    List<CommunityPost> findByPublishedAtGreaterThanEqualAndPublishedAtLessThan(Instant from, Instant to);

    @Query("""
            select post
            from CommunityPost post
            where (:source is null or post.source = :source)
              and post.publishedAt >= :publishedFrom
              and post.publishedAt < :publishedTo
            order by post.publishedAt asc, post.id asc
            """)
    List<CommunityPost> findForReactionExport(
            @Param("source") String source,
            @Param("publishedFrom") Instant publishedFrom,
            @Param("publishedTo") Instant publishedTo,
            Pageable pageable
    );

    long deleteByPublishedAtBefore(Instant cutoff);
}
