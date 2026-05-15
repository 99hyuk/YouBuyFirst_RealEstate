package com.youbuyfirst.backend.admin;

import com.youbuyfirst.backend.crawl.CrawlRun;
import com.youbuyfirst.backend.crawl.CrawlRunStatus;

import java.time.Instant;

public record CrawlRunView(
        Long id,
        String source,
        String runId,
        Instant startedAt,
        Instant finishedAt,
        CrawlRunStatus status,
        int postsSeen,
        int postsAccepted,
        String errorMessage,
        String targetId,
        String targetKind,
        String backoffCategory,
        Instant backoffUntil,
        String backoffReason,
        String skipReason
) {
    public static CrawlRunView from(CrawlRun run) {
        return new CrawlRunView(
                run.getId(),
                run.getSource(),
                run.getExternalRunId(),
                run.getStartedAt(),
                run.getFinishedAt(),
                run.getStatus(),
                run.getPostsSeen(),
                run.getPostsAccepted(),
                run.getErrorMessage(),
                run.getTargetId(),
                run.getTargetKind(),
                run.getBackoffCategory(),
                run.getBackoffUntil(),
                run.getBackoffReason(),
                run.getSkipReason()
        );
    }
}
