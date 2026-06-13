package com.youbuyfirst.backend.realestate.dto;

import java.time.Instant;

public record RealEstateContentItemResponse(
        String contentId,
        String sourceId,
        String contentType,
        String title,
        String snippet,
        String url,
        String domain,
        Instant publishedAt,
        String metricLabel,
        String statusLabel,
        Instant ingestedAt,
        String dataStatus,
        String targetId,
        String linkType,
        Double confidence,
        String reviewState
) {
}
