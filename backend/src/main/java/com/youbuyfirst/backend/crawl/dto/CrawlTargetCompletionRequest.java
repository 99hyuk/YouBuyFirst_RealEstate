package com.youbuyfirst.backend.crawl.dto;

import com.youbuyfirst.backend.crawl.CrawlRunStatus;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;

public record CrawlTargetCompletionRequest(
        @NotBlank String workerId,
        @NotNull CrawlRunStatus status,
        Instant startedAt,
        Instant finishedAt,
        @Min(0) Integer postsSeen,
        @Min(0) Integer postsAccepted,
        String backoffCategory,
        Instant backoffUntil,
        String backoffReason,
        String skipReason,
        String errorMessage
) {
}
