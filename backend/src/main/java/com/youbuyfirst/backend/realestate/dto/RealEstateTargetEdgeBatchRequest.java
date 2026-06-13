package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateTargetEdgeBatchRequest(
        List<RealEstateTargetEdgeRequest> items
) {
}
