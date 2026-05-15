package com.youbuyfirst.backend.crawl;

import jakarta.persistence.LockModeType;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface CrawlTargetRepository extends JpaRepository<CrawlTarget, Long> {

    List<CrawlTarget> findByOrderByPriorityAscTargetIdAsc(Pageable pageable);

    Optional<CrawlTarget> findByTargetId(String targetId);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("""
            select target from CrawlTarget target
            where target.status = :status
              and upper(target.source) in :sources
              and target.nextAttemptAt <= :now
              and (target.backoffUntil is null or target.backoffUntil <= :now)
              and (target.leasedUntil is null or target.leasedUntil <= :now)
            order by target.priority asc, target.targetId asc
            """)
    List<CrawlTarget> findClaimable(
            @Param("status") CrawlTargetStatus status,
            @Param("sources") Collection<String> sources,
            @Param("now") Instant now,
            Pageable pageable
    );
}
