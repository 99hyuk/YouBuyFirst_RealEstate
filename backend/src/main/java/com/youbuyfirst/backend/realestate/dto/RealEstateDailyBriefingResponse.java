package com.youbuyfirst.backend.realestate.dto;

import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public record RealEstateDailyBriefingResponse(
        String briefingId,
        LocalDate briefingDate,
        String title,
        List<String> summaryHeadlines,
        List<RealEstateDailyBriefingSectionResponse> sections,
        List<Map<String, Object>> focusRegions,
        String modelName,
        String promptVersion,
        Instant generatedAt,
        List<RealEstateDailyBriefingSourceItemResponse> sourceItems
) {
}
