package com.youbuyfirst.backend.market;

import jakarta.persistence.LockModeType;
import jakarta.persistence.QueryHint;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.QueryHints;
import org.springframework.data.repository.query.Param;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface ChartCandleRefreshRequestRepository extends JpaRepository<ChartCandleRefreshRequest, Long> {

    Optional<ChartCandleRefreshRequest> findBySymbolIgnoreCaseAndRangeLabelAndCandleInterval(
            String symbol,
            String rangeLabel,
            String candleInterval
    );

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "-2"))
    @Query("""
            select request
            from ChartCandleRefreshRequest request
            where request.status in :statuses
            order by request.requestedAt asc
            """)
    List<ChartCandleRefreshRequest> findClaimable(
            @Param("statuses") Collection<String> statuses,
            Pageable pageable
    );

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "-2"))
    @Query("""
            select request
            from ChartCandleRefreshRequest request
            where request.status = :status
              and (request.lastAttemptAt is null or request.lastAttemptAt <= :timedOutBefore)
            order by request.requestedAt asc
            """)
    List<ChartCandleRefreshRequest> findTimedOutInProgress(
            @Param("status") String status,
            @Param("timedOutBefore") Instant timedOutBefore,
            Pageable pageable
    );
}
