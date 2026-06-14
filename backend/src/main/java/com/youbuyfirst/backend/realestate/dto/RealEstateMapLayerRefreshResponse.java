package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateMapLayerRefreshResponse(
        String layerType,
        List<String> periods,
        String asOf,
        int acceptedSnapshots,
        int skippedTargets
) {
}
