package com.youbuyfirst.backend.realestate;

import java.math.BigDecimal;
import java.time.Instant;

public record MapLayerSnapshotRow(
        String targetId,
        String targetType,
        String displayName,
        String slug,
        String regionLevel,
        String regionCode,
        String legalDongCode,
        String parentTargetId,
        String geometryId,
        String periodKey,
        BigDecimal changePct,
        int sampleCount,
        BigDecimal confidence,
        Instant asOf,
        String provider,
        String sourceLabel,
        String dataStatus,
        boolean stale,
        String assetSourceLabel
) {
}
