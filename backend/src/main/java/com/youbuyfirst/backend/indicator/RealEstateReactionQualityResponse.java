package com.youbuyfirst.backend.indicator;

public record RealEstateReactionQualityResponse(
        double confidence,
        int sourceCount,
        double sourceSkew,
        String coverageStatus,
        boolean stale
) {
}
