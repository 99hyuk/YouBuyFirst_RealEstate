package com.humanindicator.backend.ingestion.dto;

import com.humanindicator.backend.crawl.CrawlRunStatus;
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
        String errorMessage
) {
}
