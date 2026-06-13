package com.youbuyfirst.backend.realestate.dto;

public record RealEstateRegionImportResponse(
        int acceptedRegions,
        int ensuredMarketDataTargets
) {
}
