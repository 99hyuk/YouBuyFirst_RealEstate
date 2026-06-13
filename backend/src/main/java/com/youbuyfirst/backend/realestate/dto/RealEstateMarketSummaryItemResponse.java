package com.youbuyfirst.backend.realestate.dto;

public record RealEstateMarketSummaryItemResponse(
        String label,
        String value,
        Double changePct,
        String updatedLabel,
        String trend,
        String dataStatus,
        boolean stale,
        String provider,
        String factType,
        String legalDongCode
) {
}
