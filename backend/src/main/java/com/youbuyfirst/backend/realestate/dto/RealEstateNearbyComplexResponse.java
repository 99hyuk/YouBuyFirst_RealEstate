package com.youbuyfirst.backend.realestate.dto;

public record RealEstateNearbyComplexResponse(
        String targetId,
        String name,
        String address,
        String region,
        Double latitude,
        Double longitude,
        String tone,
        String price,
        String change,
        String reaction,
        String provider,
        String asOf,
        String dataStatus,
        boolean stale,
        String note,
        String legalDongCode,
        String coordinateProvider,
        String coordinateStatus
) {
}
