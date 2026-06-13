package com.youbuyfirst.backend.realestate.dto;

import java.util.Map;

public record RealEstateMapLayerTargetResponse(
        String targetId,
        String targetType,
        String displayName,
        String slug,
        String regionLevel,
        String regionCode,
        String legalDongCode,
        String parentTargetId,
        String geometryId,
        Map<String, RealEstateMapLayerPeriodResponse> periods
) {
}
