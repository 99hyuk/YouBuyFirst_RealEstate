package com.youbuyfirst.backend.instrument;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface InstrumentIdentifierRepository extends JpaRepository<InstrumentIdentifier, Long> {

    Optional<InstrumentIdentifier> findByNamespaceIgnoreCaseAndNormalizedIdentifierAndPurposeIgnoreCaseAndEnabledTrue(
            String namespace,
            String normalizedIdentifier,
            String purpose
    );

    List<InstrumentIdentifier> findByInstrumentAndEnabledTrueOrderByNamespaceAscPurposeAscIdentifierAsc(Instrument instrument);
}
