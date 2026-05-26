package com.youbuyfirst.backend.instrument;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;

@Entity
@Table(
        name = "instrument_alias_candidates",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_alias_candidate_source_alias_symbol",
                columnNames = {"source", "normalized_alias", "suggested_market", "suggested_symbol"}
        )
)
public class InstrumentAliasCandidate {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 40)
    private String source;

    @Column(nullable = false, length = 200)
    private String alias;

    @Column(name = "normalized_alias", nullable = false, length = 200)
    private String normalizedAlias;

    @Column(name = "suggested_market", length = 20)
    private String suggestedMarket;

    @Column(name = "suggested_symbol", length = 40)
    private String suggestedSymbol;

    @Column(nullable = false, length = 80)
    private String reason;

    @Column(name = "context_snippet", length = 500)
    private String contextSnippet;

    @Column(name = "sample_url", length = 1000)
    private String sampleUrl;

    @Column(name = "first_seen_at", nullable = false)
    private Instant firstSeenAt;

    @Column(name = "last_seen_at", nullable = false)
    private Instant lastSeenAt;

    @Column(name = "occurrence_count", nullable = false)
    private Integer occurrenceCount;

    @Column(nullable = false, length = 40)
    private String status;

    @Column(length = 80)
    private String reviewer;

    @Column(name = "review_notes", length = 500)
    private String reviewNotes;

    @Column(name = "reviewed_at")
    private Instant reviewedAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected InstrumentAliasCandidate() {
    }

    public InstrumentAliasCandidate(
            String source,
            String alias,
            String normalizedAlias,
            String suggestedMarket,
            String suggestedSymbol,
            String reason,
            String contextSnippet,
            String sampleUrl,
            Instant observedAt,
            Instant createdAt
    ) {
        this.source = source;
        this.alias = alias;
        this.normalizedAlias = normalizedAlias;
        this.suggestedMarket = suggestedMarket;
        this.suggestedSymbol = suggestedSymbol;
        this.reason = reason;
        this.contextSnippet = contextSnippet;
        this.sampleUrl = sampleUrl;
        this.firstSeenAt = observedAt;
        this.lastSeenAt = observedAt;
        this.occurrenceCount = 1;
        this.status = "PENDING";
        this.createdAt = createdAt;
        this.updatedAt = createdAt;
    }

    public void recordSeen(String reason, String contextSnippet, String sampleUrl, Instant observedAt, Instant updatedAt) {
        this.reason = reason;
        if (contextSnippet != null) {
            this.contextSnippet = contextSnippet;
        }
        if (sampleUrl != null) {
            this.sampleUrl = sampleUrl;
        }
        if (observedAt.isBefore(this.firstSeenAt)) {
            this.firstSeenAt = observedAt;
        }
        if (observedAt.isAfter(this.lastSeenAt)) {
            this.lastSeenAt = observedAt;
        }
        this.occurrenceCount += 1;
        this.updatedAt = updatedAt;
    }

    public void markReviewed(String status, String reviewer, String reviewNotes, Instant reviewedAt) {
        this.status = status;
        this.reviewer = reviewer;
        this.reviewNotes = reviewNotes;
        this.reviewedAt = reviewedAt;
        this.updatedAt = reviewedAt;
    }

    public void markPromoted(String reviewer, String reviewNotes, Instant reviewedAt) {
        markReviewed("PROMOTED", reviewer, reviewNotes, reviewedAt);
    }

    public Long getId() {
        return id;
    }

    public String getSource() {
        return source;
    }

    public String getAlias() {
        return alias;
    }

    public String getNormalizedAlias() {
        return normalizedAlias;
    }

    public String getSuggestedMarket() {
        return suggestedMarket;
    }

    public String getSuggestedSymbol() {
        return suggestedSymbol;
    }

    public String getReason() {
        return reason;
    }

    public String getContextSnippet() {
        return contextSnippet;
    }

    public String getSampleUrl() {
        return sampleUrl;
    }

    public Instant getFirstSeenAt() {
        return firstSeenAt;
    }

    public Instant getLastSeenAt() {
        return lastSeenAt;
    }

    public Integer getOccurrenceCount() {
        return occurrenceCount;
    }

    public String getStatus() {
        return status;
    }

    public String getReviewer() {
        return reviewer;
    }

    public String getReviewNotes() {
        return reviewNotes;
    }

    public Instant getReviewedAt() {
        return reviewedAt;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
