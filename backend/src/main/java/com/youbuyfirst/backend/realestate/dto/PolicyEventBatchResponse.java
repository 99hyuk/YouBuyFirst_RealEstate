package com.youbuyfirst.backend.realestate.dto;

public record PolicyEventBatchResponse(
        int acceptedEvents,
        int acceptedTargetLinks,
        int materializedTimelineEvents
) {
}
