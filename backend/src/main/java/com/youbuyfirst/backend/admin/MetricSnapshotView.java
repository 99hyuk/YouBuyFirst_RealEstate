package com.youbuyfirst.backend.admin;

import com.youbuyfirst.backend.metrics.MetricSnapshot;

import java.time.Instant;

public record MetricSnapshotView(
        String market,
        String symbol,
        Instant windowStart,
        Instant windowEnd,
        int mentionCount,
        int bullishCount,
        int bearishCount,
        int neutralCount,
        double netSentiment,
        Double momentumPercent
) {
    public static MetricSnapshotView from(MetricSnapshot snapshot) {
        return new MetricSnapshotView(
                snapshot.getInstrument().getMarket(),
                snapshot.getInstrument().getSymbol(),
                snapshot.getWindowStart(),
                snapshot.getWindowEnd(),
                snapshot.getMentionCount(),
                snapshot.getBullishCount(),
                snapshot.getBearishCount(),
                snapshot.getNeutralCount(),
                snapshot.getNetSentiment(),
                snapshot.getMomentumPercent()
        );
    }
}

