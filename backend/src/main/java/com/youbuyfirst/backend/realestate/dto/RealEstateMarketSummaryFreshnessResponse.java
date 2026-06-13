package com.youbuyfirst.backend.realestate.dto;

import java.time.LocalDate;

public record RealEstateMarketSummaryFreshnessResponse(
        int staleCount,
        int sourceCount,
        LocalDate latestAsOf,
        String dataStatus
) {
}
