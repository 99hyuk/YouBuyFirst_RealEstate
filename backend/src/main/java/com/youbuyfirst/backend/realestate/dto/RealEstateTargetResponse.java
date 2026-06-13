package com.youbuyfirst.backend.realestate.dto;

public record RealEstateTargetResponse(
        String targetId,
        String targetType,
        String displayName,
        String slug,
        String reviewState,
        String dataStatus,
        String regionLevel,
        String parentTargetId,
        String legalDongCode,
        String regionCode
) {
}
