package com.humanindicator.backend.ingestion.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;
import java.util.List;

public record IngestionRequest(
        @NotBlank String source,
        @NotBlank String runId,
        @NotNull Instant batchStartedAt,
        @NotNull Instant batchFinishedAt,
        @NotEmpty List<@Valid PostPayload> posts
) {
}

