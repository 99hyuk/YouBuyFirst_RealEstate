package com.youbuyfirst.backend.market;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface InvestorFlowSnapshotRepository extends JpaRepository<InvestorFlowSnapshot, Long> {

    Optional<InvestorFlowSnapshot> findFirstByInstrumentIdAndTradeDate(Long instrumentId, LocalDate tradeDate);

    Optional<InvestorFlowSnapshot> findBySymbolIgnoreCaseAndTradeDate(String symbol, LocalDate tradeDate);

    List<InvestorFlowSnapshot> findByInstrumentIdAndDataStatusInOrderByTradeDateDesc(
            Long instrumentId,
            Collection<String> dataStatuses,
            Pageable pageable
    );

    List<InvestorFlowSnapshot> findBySymbolIgnoreCaseAndDataStatusInOrderByTradeDateDesc(
            String symbol,
            Collection<String> dataStatuses,
            Pageable pageable
    );
}
