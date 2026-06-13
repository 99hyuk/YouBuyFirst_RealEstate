package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateAliasListResponse(
        List<RealEstateAliasResponse> items
) {
}
