package com.youbuyfirst.backend.realestate.dto;

public record RealEstateDailyBriefingBatchResponse(
        int acceptedBriefings,
        int acceptedSections,
        int acceptedSourceItems
) {
}
