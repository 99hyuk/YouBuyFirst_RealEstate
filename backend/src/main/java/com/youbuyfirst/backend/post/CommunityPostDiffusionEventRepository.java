package com.youbuyfirst.backend.post;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;

public interface CommunityPostDiffusionEventRepository extends JpaRepository<CommunityPostDiffusionEvent, Long> {

    boolean existsBySourceAndExternalIdAndDiffusionTypeAndObservedAt(
            String source,
            String externalId,
            String diffusionType,
            Instant observedAt
    );

    List<CommunityPostDiffusionEvent> findByOrderByObservedAtDesc(Pageable pageable);

    List<CommunityPostDiffusionEvent> findBySourceOrderByObservedAtDesc(String source, Pageable pageable);
}
