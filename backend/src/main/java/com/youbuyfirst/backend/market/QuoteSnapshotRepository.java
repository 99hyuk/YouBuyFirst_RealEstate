package com.youbuyfirst.backend.market;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface QuoteSnapshotRepository extends JpaRepository<QuoteSnapshot, Long> {

    Optional<QuoteSnapshot> findBySymbolIgnoreCase(String symbol);

    @Query("select snapshot from QuoteSnapshot snapshot where lower(snapshot.symbol) in :symbols")
    List<QuoteSnapshot> findBySymbolsIgnoreCase(@Param("symbols") Collection<String> symbols);
}
