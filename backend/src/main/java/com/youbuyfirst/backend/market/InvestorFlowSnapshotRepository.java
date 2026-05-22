package com.youbuyfirst.backend.market;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface InvestorFlowSnapshotRepository extends JpaRepository<InvestorFlowSnapshot, Long> {

    Optional<InvestorFlowSnapshot> findBySymbolIgnoreCase(String symbol);

    @Query("select s from InvestorFlowSnapshot s where lower(s.symbol) in :symbols")
    List<InvestorFlowSnapshot> findBySymbolsIgnoreCase(Collection<String> symbols);
}
