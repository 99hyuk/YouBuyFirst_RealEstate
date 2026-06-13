package com.youbuyfirst.backend.indicator;

import java.time.Instant;

public record RealEstateReactionRankingFreshnessResponse(
        String source,
        Instant asOf,
        int staleCount,
        int sourceCount,
        String coverageStatus
) {
}
