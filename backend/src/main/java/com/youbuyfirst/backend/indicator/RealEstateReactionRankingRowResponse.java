package com.youbuyfirst.backend.indicator;

import java.util.List;

public record RealEstateReactionRankingRowResponse(
        int rank,
        String targetId,
        String targetType,
        String displayName,
        int mentionCount,
        double mentionDeltaPct,
        RealEstateReactionRatioResponse reactionDirectionRatio,
        int heatScore,
        double confidence,
        int sourceCount,
        double sourceSkew,
        String coverageStatus,
        boolean stale,
        List<RealEstateReactionSnapshotIssueResponse> issueMix
) {
}
