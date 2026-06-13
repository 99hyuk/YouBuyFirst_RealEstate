package com.youbuyfirst.backend.realestate.dto;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public record RealEstateMarketFactStagingRequest(
        @NotBlank @Size(max = 30) String targetType,
        @Size(max = 120) String targetId,
        @Size(max = 20) String legalDongCode,
        @NotBlank @Size(max = 60) String factType,
        LocalDate observedAt,
        @NotNull LocalDate asOf,
        @NotNull JsonNode valueJson,
        @NotBlank @Size(max = 30) String validationStatus,
        String validationMessage
) {
}
