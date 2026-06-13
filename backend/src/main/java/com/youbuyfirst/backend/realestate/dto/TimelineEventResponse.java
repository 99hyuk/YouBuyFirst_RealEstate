package com.youbuyfirst.backend.realestate.dto;

import java.time.Instant;

public record TimelineEventResponse(
        String id,
        String targetId,
        String eventType,
        String sourceRefType,
        String sourceRefId,
        String title,
        String summary,
        Instant occurredAt,
        Instant asOf,
        String dataStatus
) {
}
