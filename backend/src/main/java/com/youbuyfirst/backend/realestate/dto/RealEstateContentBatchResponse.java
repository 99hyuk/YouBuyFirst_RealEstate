package com.youbuyfirst.backend.realestate.dto;

public record RealEstateContentBatchResponse(
        int acceptedItems,
        int acceptedTargetLinks,
        int materializedTimelineEvents
) {
}
