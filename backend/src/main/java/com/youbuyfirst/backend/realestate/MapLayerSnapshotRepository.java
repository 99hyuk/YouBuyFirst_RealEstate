package com.youbuyfirst.backend.realestate;

import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.Optional;

public interface MapLayerSnapshotRepository extends JpaRepository<MapLayerSnapshot, String> {

    Optional<MapLayerSnapshot> findByTargetIdAndLayerTypeAndPeriodKeyAndAsOf(
            String targetId,
            String layerType,
            String periodKey,
            Instant asOf
    );
}
