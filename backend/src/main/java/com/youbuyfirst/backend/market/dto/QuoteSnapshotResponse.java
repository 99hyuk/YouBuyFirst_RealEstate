package com.youbuyfirst.backend.market.dto;

import java.math.BigDecimal;
import java.time.Instant;

public record QuoteSnapshotResponse(
        Long instrumentId,
        String symbol,
        String name,
        String market,
        String currency,
        BigDecimal price,
        BigDecimal change,
        BigDecimal changePct,
        long volume,
        Instant asOf,
        String provider,
        String delayLabel,
        boolean stale,
        String dataStatus
) {
}
