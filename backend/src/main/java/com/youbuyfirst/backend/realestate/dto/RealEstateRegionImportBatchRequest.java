package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateRegionImportBatchRequest(
        List<RealEstateRegionImportRequest> items
) {
}
