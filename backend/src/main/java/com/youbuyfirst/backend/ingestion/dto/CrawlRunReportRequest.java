package com.youbuyfirst.backend.ingestion.dto;

import com.youbuyfirst.backend.crawl.CrawlRunStatus;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;

public record CrawlRunReportRequest(
        @NotBlank String source,
        @NotBlank String runId,
        @NotNull Instant batchStartedAt,
        Instant batchFinishedAt,
        @NotNull CrawlRunStatus status,
        @Min(0) int postsSeen,
        @Min(0) int postsAccepted,
        String errorMessage,
        String targetId,
        String targetKind,
        String backoffCategory,
        Instant backoffUntil,
        String backoffReason,
        String skipReason,
        @Min(0) Integer pagesFetched,
        @Min(0) Integer rowsSeen,
        @Min(0) Integer ignoredPinnedCount,
        Boolean duplicateStop,
        Boolean cutoffStop,
        Instant oldestSeenAt,
        Instant newestSeenAt,
        String lastCursor,
        String coverageStatus
) {
    public CrawlRunReportRequest(
            String source,
            String runId,
            Instant batchStartedAt,
            Instant batchFinishedAt,
            CrawlRunStatus status,
            int postsSeen,
            int postsAccepted,
            String errorMessage
    ) {
        this(source, runId, batchStartedAt, batchFinishedAt, status, postsSeen, postsAccepted, errorMessage, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null);
    }
}
