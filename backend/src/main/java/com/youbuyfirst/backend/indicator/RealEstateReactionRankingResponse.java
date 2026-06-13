package com.youbuyfirst.backend.indicator;

import java.time.Instant;
import java.util.List;

public record RealEstateReactionRankingResponse(
        String window,
        Instant windowStart,
        Instant windowEnd,
        RealEstateReactionRankingFreshnessResponse freshness,
        List<RealEstateReactionRankingRowResponse> items
) {
}
