package com.youbuyfirst.backend.market.dto;

import java.time.Instant;
import java.time.LocalDate;

public record InvestorFlowSnapshotResponse(
        String symbol,
        String name,
        String market,
        String currency,
        LocalDate tradeDate,
        String provider,
        String sourceLabel,
        String delayLabel,
        Instant asOf,
        boolean stale,
        String dataStatus,
        InvestorFlowLegResponse individual,
        InvestorFlowLegResponse foreign,
        InvestorFlowLegResponse institution
) {
}
