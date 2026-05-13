package com.humanindicator.backend.metrics;

import com.humanindicator.backend.instrument.Instrument;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

public interface MetricSnapshotRepository extends JpaRepository<MetricSnapshot, Long> {

    void deleteByWindowStart(Instant windowStart);

    Optional<MetricSnapshot> findFirstByInstrumentAndWindowStartBeforeOrderByWindowStartDesc(Instrument instrument, Instant windowStart);

    List<MetricSnapshot> findByInstrumentOrderByWindowStartDesc(Instrument instrument, Pageable pageable);
}

