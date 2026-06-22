package com.youbuyfirst.backend.realestate.dto;

public record RealEstateComplexRequest(
        String targetId,
        String regionTargetId,
        String legalDongCode,
        String roadAddress,
        String jibunAddress,
        String normalizedAddress,
        Integer builtYear,
        Integer householdCount,
        String source,
        java.math.BigDecimal latitude,
        java.math.BigDecimal longitude,
        String coordinateProvider,
        String coordinateAsOf,
        String coordinateStatus,
        String markerTone,
        String priceSummary,
        String changeLabel,
        String reactionSummary,
        String markerNote,
        String markerDataStatus,
        Boolean markerStale
) {
}
