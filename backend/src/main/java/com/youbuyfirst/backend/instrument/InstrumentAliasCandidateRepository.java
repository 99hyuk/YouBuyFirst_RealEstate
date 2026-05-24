package com.youbuyfirst.backend.instrument;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface InstrumentAliasCandidateRepository extends JpaRepository<InstrumentAliasCandidate, Long> {

    Optional<InstrumentAliasCandidate> findBySourceAndNormalizedAliasAndSuggestedMarketAndSuggestedSymbol(
            String source,
            String normalizedAlias,
            String suggestedMarket,
            String suggestedSymbol
    );

    List<InstrumentAliasCandidate> findByOrderByLastSeenAtDesc(Pageable pageable);

    List<InstrumentAliasCandidate> findBySourceOrderByLastSeenAtDesc(String source, Pageable pageable);

    List<InstrumentAliasCandidate> findByStatusOrderByLastSeenAtDesc(String status, Pageable pageable);

    List<InstrumentAliasCandidate> findBySourceAndStatusOrderByLastSeenAtDesc(String source, String status, Pageable pageable);
}
