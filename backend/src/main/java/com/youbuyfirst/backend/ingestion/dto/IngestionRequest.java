package com.youbuyfirst.backend.ingestion.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;
import java.util.List;

public record IngestionRequest(
        @NotBlank String source,
        @NotBlank String runId,
        @NotNull Instant batchStartedAt,
        @NotNull Instant batchFinishedAt,
        @NotNull List<@Valid PostPayload> posts,
        @Min(0) Integer pagesFetched,
        @Min(0) Integer rowsSeen,
        @Min(0) Integer ignoredPinnedCount,
        Boolean duplicateStop,
        Boolean cutoffStop,
        Instant oldestSeenAt,
        Instant newestSeenAt,
        String lastCursor,
        String coverageStatus,
        List<@Valid DiffusionPayload> diffusionEvents,
        List<@Valid CommentCollectionTargetPayload> commentCollectionTargets
) {
    public IngestionRequest(
            String source,
            String runId,
            Instant batchStartedAt,
            Instant batchFinishedAt,
            List<@Valid PostPayload> posts
    ) {
        this(source, runId, batchStartedAt, batchFinishedAt, posts, null, null, null, null, null, null, null, null, null, null, null);
    }

    public IngestionRequest(
            String source,
            String runId,
            Instant batchStartedAt,
            Instant batchFinishedAt,
            List<@Valid PostPayload> posts,
            List<@Valid DiffusionPayload> diffusionEvents
    ) {
        this(source, runId, batchStartedAt, batchFinishedAt, posts, null, null, null, null, null, null, null, null, null, diffusionEvents, null);
    }

    public IngestionRequest(
            String source,
            String runId,
            Instant batchStartedAt,
            Instant batchFinishedAt,
            List<@Valid PostPayload> posts,
            Integer pagesFetched,
            Integer rowsSeen,
            Integer ignoredPinnedCount,
            Boolean duplicateStop,
            Boolean cutoffStop,
            Instant oldestSeenAt,
            Instant newestSeenAt,
            String lastCursor,
            String coverageStatus
    ) {
        this(source, runId, batchStartedAt, batchFinishedAt, posts, pagesFetched, rowsSeen, ignoredPinnedCount, duplicateStop, cutoffStop, oldestSeenAt, newestSeenAt, lastCursor, coverageStatus, null, null);
    }
}
