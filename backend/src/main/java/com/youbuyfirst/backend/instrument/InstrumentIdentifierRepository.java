package com.youbuyfirst.backend.instrument;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.EntityGraph;

import java.util.List;
import java.util.Optional;

public interface InstrumentIdentifierRepository extends JpaRepository<InstrumentIdentifier, Long> {

    @EntityGraph(attributePaths = "instrument")
    Optional<InstrumentIdentifier> findByNamespaceIgnoreCaseAndNormalizedIdentifierAndPurposeIgnoreCaseAndEnabledTrue(
            String namespace,
            String normalizedIdentifier,
            String purpose
    );

    List<InstrumentIdentifier> findByInstrumentAndEnabledTrueOrderByNamespaceAscPurposeAscIdentifierAsc(Instrument instrument);
}
