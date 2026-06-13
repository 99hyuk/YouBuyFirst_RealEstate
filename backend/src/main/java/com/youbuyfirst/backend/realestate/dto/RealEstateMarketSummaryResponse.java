package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateMarketSummaryResponse(
        List<RealEstateMarketSummaryItemResponse> items,
        RealEstateMarketSummaryFreshnessResponse freshness
) {
}
