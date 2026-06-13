package com.youbuyfirst.backend.realestate.dto;

public record RealEstateTargetUpsertRequest(
        String targetId,
        String targetType,
        String displayName,
        String slug,
        String reviewState,
        String dataStatus
) {
}
