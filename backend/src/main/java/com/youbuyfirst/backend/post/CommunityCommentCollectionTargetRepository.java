package com.youbuyfirst.backend.post;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface CommunityCommentCollectionTargetRepository extends JpaRepository<CommunityCommentCollectionTarget, Long> {

    Optional<CommunityCommentCollectionTarget> findBySourceAndExternalId(String source, String externalId);

    List<CommunityCommentCollectionTarget> findByOrderByPriorityAscCreatedAtAsc(Pageable pageable);

    List<CommunityCommentCollectionTarget> findBySourceOrderByPriorityAscCreatedAtAsc(String source, Pageable pageable);
}
