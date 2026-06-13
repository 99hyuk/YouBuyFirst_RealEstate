package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateMarketFactListResponse(
        List<RealEstateMarketFactResponse> items
) {
}
