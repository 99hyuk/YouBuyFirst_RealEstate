package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.util.List;

public record RealEstateContentItemRequest(
        @NotBlank @Size(max = 120) String contentId,
        @Size(max = 120) String sourceId,
        @NotBlank @Size(max = 40) String contentType,
        @NotBlank @Size(max = 200) String title,
        String snippet,
        @NotBlank @Size(max = 1000) String url,
        @Size(max = 160) String domain,
        Instant publishedAt,
        @Size(max = 120) String metricLabel,
        @Size(max = 120) String statusLabel,
        @NotNull Instant ingestedAt,
        @NotBlank @Size(max = 30) String dataStatus,
        @NotNull List<@Valid RealEstateContentTargetRequest> targets
) {
}
