package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateNearbyComplexListResponse(
        String targetId,
        String dataStatus,
        boolean stale,
        List<RealEstateNearbyComplexResponse> items
) {
}
