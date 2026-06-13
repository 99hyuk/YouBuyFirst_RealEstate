package com.youbuyfirst.backend.realestate.dto;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.time.LocalDate;

public record RealEstateMarketFactRequest(
        @NotBlank @Size(max = 30) String targetType,
        @Size(max = 120) String targetId,
        @NotBlank @Size(max = 40) String factType,
        @NotBlank @Size(max = 60) String provider,
        @NotBlank @Size(max = 80) String providerDataset,
        @NotBlank @Size(max = 180) String providerObjectId,
        @NotBlank @Size(max = 20) String legalDongCode,
        @NotNull LocalDate observedAt,
        @NotNull LocalDate asOf,
        @NotNull Instant ingestedAt,
        Instant sourceUpdatedAt,
        @NotNull JsonNode valueJson,
        @NotBlank @Size(max = 30) String dataStatus,
        boolean stale
) {
}
