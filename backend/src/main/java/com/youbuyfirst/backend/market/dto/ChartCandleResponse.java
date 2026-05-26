package com.youbuyfirst.backend.market.dto;

import java.time.Instant;
import java.util.List;

public record ChartCandleResponse(
        Long instrumentId,
        String symbol,
        String name,
        String market,
        String currency,
        String range,
        String interval,
        String provider,
        String delayLabel,
        Instant asOf,
        boolean stale,
        String dataStatus,
        List<ChartCandleBarResponse> bars,
        ChartCandleDisplayPolicyResponse displayPolicy
) {
}
