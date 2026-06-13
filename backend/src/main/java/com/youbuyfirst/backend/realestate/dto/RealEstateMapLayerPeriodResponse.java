package com.youbuyfirst.backend.realestate.dto;

public record RealEstateMapLayerPeriodResponse(
        double changePct,
        int sampleCount,
        double confidence,
        String asOf,
        String provider,
        String sourceLabel,
        String dataStatus,
        boolean stale
) {
}
