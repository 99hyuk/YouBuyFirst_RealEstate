package com.youbuyfirst.backend.market;

import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface ChartCandleSetRepository extends JpaRepository<ChartCandleSet, Long> {

    @EntityGraph(attributePaths = "bars")
    Optional<ChartCandleSet> findFirstByInstrumentIdAndRangeLabelAndCandleInterval(
            Long instrumentId,
            String rangeLabel,
            String candleInterval
    );

    @EntityGraph(attributePaths = "bars")
    Optional<ChartCandleSet> findBySymbolIgnoreCaseAndRangeLabelAndCandleInterval(
            String symbol,
            String rangeLabel,
            String candleInterval
    );
}
