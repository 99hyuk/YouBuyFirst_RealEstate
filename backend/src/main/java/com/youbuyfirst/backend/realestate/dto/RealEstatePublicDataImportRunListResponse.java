package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstatePublicDataImportRunListResponse(
        List<RealEstatePublicDataImportRunResponse> items
) {
}
