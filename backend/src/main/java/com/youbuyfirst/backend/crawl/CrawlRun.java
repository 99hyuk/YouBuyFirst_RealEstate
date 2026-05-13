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

    protected CrawlRun() {
    }

    public CrawlRun(String source, String externalRunId, Instant startedAt, Instant finishedAt, CrawlRunStatus status, int postsSeen, int postsAccepted, String errorMessage) {
        this.source = source;
        this.externalRunId = externalRunId;
        this.startedAt = startedAt;
        this.finishedAt = finishedAt;
        this.status = status;
        this.postsSeen = postsSeen;
        this.postsAccepted = postsAccepted;
        this.errorMessage = errorMessage;
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
}

