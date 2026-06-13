package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "timeline_events")
public class TimelineEvent {

    @Id
    @Column(length = 360)
    private String id;

    @Column(name = "target_id", nullable = false, length = 120)
    private String targetId;

    @Column(name = "event_type", nullable = false, length = 40)
    private String eventType;

    @Column(name = "source_ref_type", nullable = false, length = 40)
    private String sourceRefType;

    @Column(name = "source_ref_id", nullable = false, length = 120)
    private String sourceRefId;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(columnDefinition = "text")
    private String summary;

    @Column(name = "occurred_at")
    private Instant occurredAt;

    @Column(name = "as_of")
    private Instant asOf;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected TimelineEvent() {
    }

    public TimelineEvent(String id, String targetId, Instant now) {
        this.id = id;
        this.targetId = targetId;
        this.createdAt = now;
    }

    public void update(
            String eventType,
            String sourceRefType,
            String sourceRefId,
            String title,
            String summary,
            Instant occurredAt,
            Instant asOf,
            String dataStatus,
            Instant now
    ) {
        this.eventType = eventType;
        this.sourceRefType = sourceRefType;
        this.sourceRefId = sourceRefId;
        this.title = title;
        this.summary = summary;
        this.occurredAt = occurredAt;
        this.asOf = asOf;
        this.dataStatus = dataStatus;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getEventType() {
        return eventType;
    }

    public String getSourceRefType() {
        return sourceRefType;
    }

    public String getSourceRefId() {
        return sourceRefId;
    }

    public String getTitle() {
        return title;
    }

    public String getSummary() {
        return summary;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }

    public Instant getAsOf() {
        return asOf;
    }

    public String getDataStatus() {
        return dataStatus;
    }
}
