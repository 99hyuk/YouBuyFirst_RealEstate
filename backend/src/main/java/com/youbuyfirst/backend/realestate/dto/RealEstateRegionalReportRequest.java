package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.util.List;

public record RealEstateRegionalReportRequest(
        @NotBlank @Size(max = 160) String reportId,
        @NotBlank @Size(max = 120) String targetId,
        @NotBlank @Size(max = 80) String reportVersion,
        @Size(max = 80) String promptVersion,
        @Size(max = 80) String modelName,
        @NotBlank @Size(max = 80) String generatedBy,
        @NotBlank @Size(max = 200) String title,
        @NotBlank @Size(max = 300) String headline,
        @NotBlank String summary,
        @NotBlank String body,
        @NotNull List<@Size(max = 240) String> expectationPoints,
        @NotNull List<@Size(max = 240) String> concernPoints,
        @NotBlank @Size(max = 30) String dataQuality,
        Double confidence,
        @NotNull Instant asOf,
        @NotNull Instant publishedAt,
        @NotNull List<@Valid RealEstateRegionalReportSourceRequest> sources
) {
}
