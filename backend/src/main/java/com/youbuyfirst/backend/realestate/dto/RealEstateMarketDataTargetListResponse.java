package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateMarketDataTargetListResponse(
        List<RealEstateMarketDataTargetResponse> items
) {
}
