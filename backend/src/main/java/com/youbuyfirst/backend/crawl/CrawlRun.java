package com.youbuyfirst.backend.crawl;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "crawl_runs")
public class CrawlRun {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 40)
    private String source;

    @Column(name = "external_run_id", nullable = false, length = 120)
    private String externalRunId;

    @Column(name = "started_at", nullable = false)
    private Instant startedAt;

    @Column(name = "finished_at")
    private Instant finishedAt;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private CrawlRunStatus status;

    @Column(name = "posts_seen", nullable = false)
    private int postsSeen;

    @Column(name = "posts_accepted", nullable = false)
    private int postsAccepted;

    @Column(name = "error_message", length = 1000)
    private String errorMessage;

    @Column(name = "target_id", length = 160)
    private String targetId;

    @Column(name = "target_kind", length = 40)
    private String targetKind;

    @Column(name = "backoff_category", length = 40)
    private String backoffCategory;

    @Column(name = "backoff_until")
    private Instant backoffUntil;

    @Column(name = "backoff_reason", length = 500)
    private String backoffReason;

    @Column(name = "skip_reason", length = 500)
    private String skipReason;

    @Column(name = "pages_fetched")
    private Integer pagesFetched;

    @Column(name = "rows_seen")
    private Integer rowsSeen;

    @Column(name = "ignored_pinned_count")
    private Integer ignoredPinnedCount;

    @Column(name = "duplicate_stop")
    private Boolean duplicateStop;

    @Column(name = "cutoff_stop")
    private Boolean cutoffStop;

    @Column(name = "oldest_seen_at")
    private Instant oldestSeenAt;

    @Column(name = "newest_seen_at")
    private Instant newestSeenAt;

    @Column(name = "last_cursor", length = 120)
    private String lastCursor;

    @Column(name = "coverage_status", length = 40)
    private String coverageStatus;

    protected CrawlRun() {
    }

    public CrawlRun(String source, String externalRunId, Instant startedAt, Instant finishedAt, CrawlRunStatus status, int postsSeen, int postsAccepted, String errorMessage) {
        this(source, externalRunId, startedAt, finishedAt, status, postsSeen, postsAccepted, errorMessage, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null);
    }

    public CrawlRun(
            String source,
            String externalRunId,
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
        this(source, externalRunId, startedAt, finishedAt, status, postsSeen, postsAccepted, errorMessage, targetId, targetKind, backoffCategory, backoffUntil, backoffReason, skipReason, null, null, null, null, null, null, null, null, null);
    }

    public CrawlRun(
            String source,
            String externalRunId,
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
            String skipReason,
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
        this.source = source;
        this.externalRunId = externalRunId;
        this.startedAt = startedAt;
        this.finishedAt = finishedAt;
        this.status = status;
        this.postsSeen = postsSeen;
        this.postsAccepted = postsAccepted;
        this.errorMessage = errorMessage;
        this.targetId = targetId;
        this.targetKind = targetKind;
        this.backoffCategory = backoffCategory;
        this.backoffUntil = backoffUntil;
        this.backoffReason = backoffReason;
        this.skipReason = skipReason;
        this.pagesFetched = pagesFetched;
        this.rowsSeen = rowsSeen;
        this.ignoredPinnedCount = ignoredPinnedCount;
        this.duplicateStop = duplicateStop;
        this.cutoffStop = cutoffStop;
        this.oldestSeenAt = oldestSeenAt;
        this.newestSeenAt = newestSeenAt;
        this.lastCursor = lastCursor;
        this.coverageStatus = coverageStatus;
    }

    public Long getId() {
        return id;
    }

    public String getSource() {
        return source;
    }

    public String getExternalRunId() {
        return externalRunId;
    }

    public Instant getStartedAt() {
        return startedAt;
    }

    public Instant getFinishedAt() {
        return finishedAt;
    }

    public CrawlRunStatus getStatus() {
        return status;
    }

    public int getPostsSeen() {
        return postsSeen;
    }

    public int getPostsAccepted() {
        return postsAccepted;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getTargetKind() {
        return targetKind;
    }

    public String getBackoffCategory() {
        return backoffCategory;
    }

    public Instant getBackoffUntil() {
        return backoffUntil;
    }

    public String getBackoffReason() {
        return backoffReason;
    }

    public String getSkipReason() {
        return skipReason;
    }

    public Integer getPagesFetched() {
        return pagesFetched;
    }

    public Integer getRowsSeen() {
        return rowsSeen;
    }

    public Integer getIgnoredPinnedCount() {
        return ignoredPinnedCount;
    }

    public Boolean getDuplicateStop() {
        return duplicateStop;
    }

    public Boolean getCutoffStop() {
        return cutoffStop;
    }

    public Instant getOldestSeenAt() {
        return oldestSeenAt;
    }

    public Instant getNewestSeenAt() {
        return newestSeenAt;
    }

    public String getLastCursor() {
        return lastCursor;
    }

    public String getCoverageStatus() {
        return coverageStatus;
    }
}
