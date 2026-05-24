package com.youbuyfirst.backend.ingestion.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;

public record AliasCandidatePayload(
        @NotBlank String alias,
        String suggestedMarket,
        String suggestedSymbol,
        @NotBlank String reason,
        String contextSnippet,
        String sampleUrl,
        @NotNull Instant observedAt
) {
}
