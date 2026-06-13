package com.youbuyfirst.backend.realestate.dto;

public record RealEstateRegionImportRequest(
        String targetId,
        String displayName,
        String slug,
        String regionLevel,
        String parentTargetId,
        String legalDongCode,
        String regionCode,
        String source
) {
}
