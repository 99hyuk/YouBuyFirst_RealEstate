package com.youbuyfirst.backend.realestate.dto;

import java.time.Instant;

public record MarketDataSourceLinkResponse(
        String id,
        String title,
        String label,
        String link,
        String provider,
        String status,
        String dataStatus,
        boolean stale,
        Instant lastCheckedAt
) {
}
