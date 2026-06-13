package com.youbuyfirst.backend.realestate.dto;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.Instant;
import java.time.LocalDate;

public record RealEstatePublicDataRunRequest(
        @NotBlank @Size(max = 180) String runKey,
        @NotBlank @Size(max = 100) String providerDataset,
        @NotBlank @Size(max = 40) String runType,
        LocalDate requestedFrom,
        LocalDate requestedTo,
        @NotNull JsonNode requestParams,
        @NotBlank @Size(max = 30) String status,
        @NotNull Instant startedAt,
        Instant finishedAt,
        String errorMessage
) {
}
