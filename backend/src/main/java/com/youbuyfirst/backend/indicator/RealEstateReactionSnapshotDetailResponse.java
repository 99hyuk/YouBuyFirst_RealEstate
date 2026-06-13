package com.youbuyfirst.backend.indicator;

import java.time.Instant;
import java.util.List;

public record RealEstateReactionSnapshotDetailResponse(
        String targetId,
        String targetType,
        String displayName,
        String window,
        Instant windowStart,
        Instant windowEnd,
        int mentionCount,
        int previousMentionCount,
        double mentionDeltaPct,
        String dominantDirection,
        RealEstateReactionRatioResponse reactionDirectionRatio,
        int heatScore,
        RealEstateReactionQualityResponse quality,
        RealEstateReactionRankingFreshnessResponse freshness,
        List<RealEstateReactionSnapshotIssueResponse> issueMix
) {
}
