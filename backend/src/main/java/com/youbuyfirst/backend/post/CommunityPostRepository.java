package com.youbuyfirst.backend.post;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;

public interface CommunityPostRepository extends JpaRepository<CommunityPost, Long> {

    boolean existsBySourceAndExternalId(String source, String externalId);

    List<CommunityPost> findByOrderByPublishedAtDesc(Pageable pageable);

    List<CommunityPost> findBySourceOrderByPublishedAtDesc(String source, Pageable pageable);

    List<CommunityPost> findByPublishedAtGreaterThanEqualAndPublishedAtLessThan(Instant from, Instant to);

    long deleteByPublishedAtBefore(Instant cutoff);
}
