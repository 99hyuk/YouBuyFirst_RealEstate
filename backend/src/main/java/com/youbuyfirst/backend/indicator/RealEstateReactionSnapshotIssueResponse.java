package com.youbuyfirst.backend.indicator;

public record RealEstateReactionSnapshotIssueResponse(
        String issueKey,
        String label,
        double share,
        String direction,
        String summary,
        double confidence
) {
}
