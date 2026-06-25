package com.youbuyfirst.backend.realestate.dto;

import java.time.Instant;

public record RealEstateRegionalReportSourceResponse(
        String reportSourceId,
        int displayOrder,
        String refType,
        String refId,
        String label,
        String title,
        String url,
        String sourceName,
        Instant publishedAt,
        String dataStatus
) {
}
