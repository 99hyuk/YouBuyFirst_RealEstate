package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateComplexBatchRequest(
        List<RealEstateComplexRequest> items
) {
}
