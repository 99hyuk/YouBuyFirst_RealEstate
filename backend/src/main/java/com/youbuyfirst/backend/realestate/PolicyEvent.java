package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "policy_events")
public class PolicyEvent {

    @Id
    @Column(length = 120)
    private String id;

    @Column(name = "event_type", nullable = false, length = 40)
    private String eventType;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(columnDefinition = "text")
    private String summary;

    @Column(name = "source_url", length = 1000)
    private String sourceUrl;

    @Column(name = "published_at")
    private Instant publishedAt;

    @Column(name = "effective_from")
    private Instant effectiveFrom;

    @Column(name = "effective_to")
    private Instant effectiveTo;

    @Column(name = "target_scope", nullable = false, length = 40)
    private String targetScope;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected PolicyEvent() {
    }

    public PolicyEvent(String id, Instant now) {
        this.id = id;
        this.createdAt = now;
    }

    public void update(
            String eventType,
            String title,
            String summary,
            String sourceUrl,
            Instant publishedAt,
            Instant effectiveFrom,
            Instant effectiveTo,
            String targetScope,
            String dataStatus,
            Instant now
    ) {
        this.eventType = eventType;
        this.title = title;
        this.summary = summary;
        this.sourceUrl = sourceUrl;
        this.publishedAt = publishedAt;
        this.effectiveFrom = effectiveFrom;
        this.effectiveTo = effectiveTo;
        this.targetScope = targetScope;
        this.dataStatus = dataStatus;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getEventType() {
        return eventType;
    }

    public String getTitle() {
        return title;
    }

    public String getSummary() {
        return summary;
    }

    public Instant getPublishedAt() {
        return publishedAt;
    }

    public Instant getEffectiveFrom() {
        return effectiveFrom;
    }

    public String getDataStatus() {
        return dataStatus;
    }
}
