package com.youbuyfirst.backend.instrument;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

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
}
