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

    protected CrawlRun() {
    }

    public CrawlRun(String source, String externalRunId, Instant startedAt, Instant finishedAt, CrawlRunStatus status, int postsSeen, int postsAccepted, String errorMessage) {
        this(source, externalRunId, startedAt, finishedAt, status, postsSeen, postsAccepted, errorMessage, null, null, null, null, null, null);
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
}
