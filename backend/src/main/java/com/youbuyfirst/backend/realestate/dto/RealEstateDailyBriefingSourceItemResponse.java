package com.youbuyfirst.backend.realestate.dto;

public record RealEstateDailyBriefingSourceItemResponse(
        String sourceItemId,
        String sourceType,
        String refId,
        String label,
        String title,
        String url,
        int displayOrder
) {
}
