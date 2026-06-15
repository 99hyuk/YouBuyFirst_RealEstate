package com.youbuyfirst.backend.realestate.dto;

import java.time.Instant;

public record RealEstateEvidenceItemResponse(
        String evidenceItemId,
        String evidenceType,
        String refType,
        String refId,
        String label,
        String valueText,
        String severity,
        String sourceUrl,
        String sourceId,
        String sourceDomain,
        Instant publishedAt,
        Instant sourceAsOf,
        String sourceDataStatus
) {
}
