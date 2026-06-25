package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.time.Instant;

public record RealEstateRegionalReportSourceRequest(
        @Size(max = 160) String reportSourceId,
        @NotBlank @Size(max = 60) String refType,
        @Size(max = 160) String refId,
        @NotBlank @Size(max = 120) String label,
        @NotBlank @Size(max = 240) String title,
        String url,
        @Size(max = 160) String sourceName,
        Instant publishedAt,
        @NotBlank @Size(max = 30) String dataStatus
) {
}
