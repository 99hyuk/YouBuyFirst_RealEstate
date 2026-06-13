package com.youbuyfirst.backend.realestate.dto;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.time.LocalDate;

public record RealEstatePublicDataRawItemRequest(
        @Size(max = 100) String providerDataset,
        @NotBlank @Size(max = 240) String providerObjectId,
        @Size(max = 20) String legalDongCode,
        @Size(max = 120) String targetId,
        LocalDate observedAt,
        @NotNull LocalDate asOf,
        Instant sourceUpdatedAt,
        @NotNull JsonNode rawPayload,
        @NotBlank @Size(max = 30) String landingStatus,
        @Valid RealEstateMarketFactStagingRequest staging
) {
}
