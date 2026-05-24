package com.youbuyfirst.backend.market.dto;

import java.time.Instant;

public record TechnicalIndicatorResponse(
        String symbol,
        String name,
        String market,
        String currency,
        String range,
        String interval,
        String provider,
        String sourceProvider,
        String delayLabel,
        Instant asOf,
        boolean stale,
        String dataStatus,
        RsiResponse rsi,
        BollingerBandsResponse bollingerBands
) {
}
