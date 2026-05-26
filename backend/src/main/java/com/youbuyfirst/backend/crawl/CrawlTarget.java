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
import java.util.Objects;

@Entity
@Table(name = "crawl_targets")
public class CrawlTarget {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 40)
    private String source;

    @Column(name = "target_id", nullable = false, length = 160)
    private String targetId;

    @Column(name = "target_kind", nullable = false, length = 40)
    private String targetKind;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private CrawlTargetStatus status;

    @Column(name = "instrument_id")
    private Long instrumentId;

    @Column(length = 20)
    private String market;

    @Column(length = 40)
    private String symbol;

    @Column(length = 1000)
    private String url;

    @Column(length = 200)
    private String label;

    @Column(nullable = false)
    private int priority;

    @Column(name = "crawl_interval_seconds", nullable = false)
    private int crawlIntervalSeconds;

    @Column(name = "next_attempt_at", nullable = false)
    private Instant nextAttemptAt;

    @Column(name = "last_attempt_at")
    private Instant lastAttemptAt;

    @Column(name = "last_success_at")
    private Instant lastSuccessAt;

    @Column(name = "last_status", length = 20)
    private String lastStatus;

    @Column(name = "consecutive_failures", nullable = false)
    private int consecutiveFailures;

    @Column(name = "backoff_category", length = 40)
    private String backoffCategory;

    @Column(name = "backoff_until")
    private Instant backoffUntil;

    @Column(name = "backoff_reason", length = 500)
    private String backoffReason;

    @Column(name = "lease_owner", length = 120)
    private String leaseOwner;

    @Column(name = "leased_until")
    private Instant leasedUntil;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected CrawlTarget() {
    }

    public void claim(String workerId, Instant now, Instant leasedUntil) {
        this.leaseOwner = clip(Objects.requireNonNull(workerId, "workerId"), 120);
        this.leasedUntil = Objects.requireNonNull(leasedUntil, "leasedUntil");
        this.lastAttemptAt = Objects.requireNonNull(now, "now");
        this.updatedAt = now;
    }

    public boolean isLeasedToAnotherWorker(String workerId, Instant now) {
        return leaseOwner != null
                && leasedUntil != null
                && leasedUntil.isAfter(now)
                && !leaseOwner.equals(workerId);
    }

    public void markCompleted(CrawlRunStatus status, Instant finishedAt, Integer postsSeen, Integer postsAccepted, String backoffCategory, Instant backoffUntil, String backoffReason) {
        Instant completedAt = Objects.requireNonNull(finishedAt, "finishedAt");
        CrawlRunStatus completedStatus = Objects.requireNonNull(status, "status");
        this.lastStatus = completedStatus.name();
        this.updatedAt = completedAt;
        this.leaseOwner = null;
        this.leasedUntil = null;

        if (completedStatus == CrawlRunStatus.SUCCESS || completedStatus == CrawlRunStatus.SKIPPED) {
            this.lastSuccessAt = completedStatus == CrawlRunStatus.SUCCESS ? completedAt : this.lastSuccessAt;
            this.consecutiveFailures = 0;
            clearBackoff();
            this.nextAttemptAt = completedAt.plusSeconds(crawlIntervalSeconds);
            return;
        }

        this.consecutiveFailures += 1;
        this.backoffCategory = clip(backoffCategory, 40);
        this.backoffUntil = backoffUntil;
        this.backoffReason = clip(backoffReason, 500);
        this.nextAttemptAt = backoffUntil != null ? backoffUntil : completedAt.plusSeconds(crawlIntervalSeconds);
    }

    private void clearBackoff() {
        this.backoffCategory = null;
        this.backoffUntil = null;
        this.backoffReason = null;
    }

    private static String clip(String value, int maxLength) {
        if (value == null || value.length() <= maxLength) {
            return value;
        }
        return value.substring(0, maxLength);
    }

    public Long getId() {
        return id;
    }

    public String getSource() {
        return source;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getTargetKind() {
        return targetKind;
    }

    public CrawlTargetStatus getStatus() {
        return status;
    }

    public Long getInstrumentId() {
        return instrumentId;
    }

    public String getMarket() {
        return market;
    }

    public String getSymbol() {
        return symbol;
    }

    public String getUrl() {
        return url;
    }

    public String getLabel() {
        return label;
    }

    public int getPriority() {
        return priority;
    }

    public int getCrawlIntervalSeconds() {
        return crawlIntervalSeconds;
    }

    public Instant getNextAttemptAt() {
        return nextAttemptAt;
    }

    public Instant getLastAttemptAt() {
        return lastAttemptAt;
    }

    public Instant getLastSuccessAt() {
        return lastSuccessAt;
    }

    public String getLastStatus() {
        return lastStatus;
    }

    public int getConsecutiveFailures() {
        return consecutiveFailures;
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

    public String getLeaseOwner() {
        return leaseOwner;
    }

    public Instant getLeasedUntil() {
        return leasedUntil;
    }
}
