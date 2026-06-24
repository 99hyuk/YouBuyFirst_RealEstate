package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public record RealEstateDailyBriefingRequest(
        @NotBlank @Size(max = 120) String briefingId,
        @NotNull LocalDate briefingDate,
        @NotBlank @Size(max = 200) String title,
        @NotNull List<@Size(max = 120) String> summaryHeadlines,
        @NotNull List<@Valid RealEstateDailyBriefingSectionRequest> sections,
        List<Map<String, Object>> focusRegions,
        @Size(max = 80) String modelName,
        @Size(max = 80) String promptVersion,
        @NotNull Instant generatedAt,
        @NotNull List<@Valid RealEstateDailyBriefingSourceItemRequest> sourceItems
) {
}
