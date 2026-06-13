package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateTargetEdgeGraphResponse(
        String targetId,
        String direction,
        List<RealEstateTargetEdgeResponse> items
) {
}
