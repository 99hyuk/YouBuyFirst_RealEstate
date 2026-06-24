package com.youbuyfirst.backend.realestate.dto;

import java.time.Instant;
import java.time.LocalDate;

public record MarketDataScheduleEventResponse(
        String id,
        LocalDate date,
        String title,
        String category,
        String source,
        String summary,
        String link,
        String tone,
        String provider,
        String status,
        String dataStatus,
        boolean stale,
        Instant lastCheckedAt,
        LocalDate asOf
) {
}
