package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateTargetListResponse(
        List<RealEstateTargetResponse> items
) {
}
