package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateContentListResponse(
        List<RealEstateContentItemResponse> items
) {
}
