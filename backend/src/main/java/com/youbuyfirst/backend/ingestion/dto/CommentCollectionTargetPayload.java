package com.youbuyfirst.backend.ingestion.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;

public record CommentCollectionTargetPayload(
        @NotBlank String externalId,
        String boardId,
        @NotBlank String triggerReason,
        @NotNull Instant triggeredAt,
        @Min(1) Integer maxComments,
        @Min(0) Integer priority,
        @Min(0) Integer viewCount,
        @Min(0) Integer recommendCount,
        @Min(0) Integer commentCount
) {
}
