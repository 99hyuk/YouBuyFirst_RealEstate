package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateMapLayerResponse(
        String layerType,
        String parentTargetId,
        String parentRegionCode,
        String asOf,
        String sourceLabel,
        String mapDataSource,
        String dataStatus,
        boolean stale,
        List<String> periods,
        List<RealEstateMapLayerTargetResponse> targets
) {
}
