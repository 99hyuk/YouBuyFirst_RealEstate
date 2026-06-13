package com.youbuyfirst.backend.realestate.dto;

public record RealEstateMarketDataTargetResponse(
        String targetId,
        String provider,
        String providerDataset,
        String lawdCode,
        boolean enabled,
        int refreshIntervalHours,
        int staleAfterHours
) {
}
