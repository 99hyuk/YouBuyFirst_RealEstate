package com.youbuyfirst.backend.market;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface ChartCandleRefreshRequestRepository extends JpaRepository<ChartCandleRefreshRequest, Long> {

    Optional<ChartCandleRefreshRequest> findBySymbolIgnoreCaseAndRangeLabelAndCandleInterval(
            String symbol,
            String rangeLabel,
            String candleInterval
    );

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
}
