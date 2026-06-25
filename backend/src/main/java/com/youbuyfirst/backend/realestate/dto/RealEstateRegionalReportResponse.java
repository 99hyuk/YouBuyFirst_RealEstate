package com.youbuyfirst.backend.realestate.dto;

import java.time.Instant;
import java.util.List;

public record RealEstateRegionalReportResponse(
        String reportId,
        String targetId,
        String targetName,
        String regionLevel,
        String regionCode,
        String reportVersion,
        String promptVersion,
        String modelName,
        String generatedBy,
        String title,
        String headline,
        String summary,
        String body,
        List<String> expectationPoints,
        List<String> concernPoints,
        String dataQuality,
        Double confidence,
        Instant asOf,
        Instant publishedAt,
        List<RealEstateRegionalReportSourceResponse> sources
) {
}
