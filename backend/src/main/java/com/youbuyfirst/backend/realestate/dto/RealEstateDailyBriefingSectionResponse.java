package com.youbuyfirst.backend.realestate.dto;

public record RealEstateDailyBriefingSectionResponse(
        String sectionId,
        String title,
        String body,
        int displayOrder
) {
}
