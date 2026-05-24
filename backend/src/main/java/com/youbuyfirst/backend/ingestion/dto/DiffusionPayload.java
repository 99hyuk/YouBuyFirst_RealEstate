package com.youbuyfirst.backend.ingestion.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;

public record DiffusionPayload(
        @NotBlank String externalId,
        String boardId,
        @NotBlank String diffusionType,
        @Min(1) Integer listPosition,
        @NotNull Instant observedAt,
        @Min(0) Integer viewCount,
        @Min(0) Integer recommendCount,
        @Min(0) Integer commentCount,
        Boolean diffusionOnly
) {
}
