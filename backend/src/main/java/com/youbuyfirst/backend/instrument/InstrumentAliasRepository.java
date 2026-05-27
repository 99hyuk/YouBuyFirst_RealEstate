package com.youbuyfirst.backend.instrument;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface InstrumentAliasRepository extends JpaRepository<InstrumentAlias, Long> {

    List<InstrumentAlias> findByOrderByAliasAsc(Pageable pageable);

    List<InstrumentAlias> findByInstrumentMarketIgnoreCaseOrderByAliasAsc(String market, Pageable pageable);

    List<InstrumentAlias> findByStatusIgnoreCaseOrderByAliasAsc(String status, Pageable pageable);

    List<InstrumentAlias> findByInstrumentMarketIgnoreCaseAndStatusIgnoreCaseOrderByAliasAsc(
            String market,
            String status,
            Pageable pageable
    );

    List<InstrumentAlias> findByNormalizedAliasAndStatusIgnoreCaseAndAmbiguousFalse(String normalizedAlias, String status);

    @Query("""
            select new com.youbuyfirst.backend.instrument.InstrumentAliasSnapshotRow(ia.instrument.id, ia.alias)
            from InstrumentAlias ia
            where upper(ia.status) = 'ACCEPTED'
              and ia.ambiguous = false
              and (:market is null or upper(ia.instrument.market) = upper(:market))
            order by ia.instrument.market asc, ia.instrument.symbol asc, ia.alias asc
            """)
    List<InstrumentAliasSnapshotRow> findMatcherSnapshotAliases(@Param("market") String market);
}
