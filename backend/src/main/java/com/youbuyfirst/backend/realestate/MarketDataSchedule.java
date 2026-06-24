package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(name = "market_data_schedules")
public class MarketDataSchedule {

    @Id
    @Column(length = 140)
    private String id;

    @Column(name = "source_id", nullable = false, length = 80)
    private String sourceId;

    @Column(name = "schedule_date", nullable = false)
    private LocalDate scheduleDate;

    @Column(nullable = false, length = 160)
    private String title;

    @Column(nullable = false, length = 40)
    private String category;

    @Column(name = "source_title", nullable = false, length = 120)
    private String sourceTitle;

    @Column(nullable = false, length = 500)
    private String summary;

    @Column(name = "source_url", nullable = false, length = 1000)
    private String sourceUrl;

    @Column(nullable = false, length = 40)
    private String tone;

    @Column(nullable = false, length = 80)
    private String provider;

    @Column(nullable = false, length = 40)
    private String status;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(nullable = false)
    private boolean stale;

    @Column(name = "last_checked_at")
    private Instant lastCheckedAt;

    @Column(name = "as_of")
    private LocalDate asOf;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected MarketDataSchedule() {
    }

    public MarketDataSchedule(String id, Instant now) {
        this.id = id;
        this.createdAt = now;
    }

    public void update(
            String sourceId,
            LocalDate scheduleDate,
            String title,
            String category,
            String sourceTitle,
            String summary,
            String sourceUrl,
            String tone,
            String provider,
            String status,
            String dataStatus,
            boolean stale,
            Instant lastCheckedAt,
            LocalDate asOf,
            Instant now
    ) {
        this.sourceId = sourceId;
        this.scheduleDate = scheduleDate;
        this.title = title;
        this.category = category;
        this.sourceTitle = sourceTitle;
        this.summary = summary;
        this.sourceUrl = sourceUrl;
        this.tone = tone;
        this.provider = provider;
        this.status = status;
        this.dataStatus = dataStatus;
        this.stale = stale;
        this.lastCheckedAt = lastCheckedAt;
        this.asOf = asOf;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getSourceId() {
        return sourceId;
    }

    public LocalDate getScheduleDate() {
        return scheduleDate;
    }

    public String getTitle() {
        return title;
    }

    public String getCategory() {
        return category;
    }

    public String getSourceTitle() {
        return sourceTitle;
    }

    public String getSummary() {
        return summary;
    }

    public String getSourceUrl() {
        return sourceUrl;
    }

    public String getTone() {
        return tone;
    }

    public String getProvider() {
        return provider;
    }

    public String getStatus() {
        return status;
    }

    public String getDataStatus() {
        return dataStatus;
    }

    public boolean isStale() {
        return stale;
    }

    public Instant getLastCheckedAt() {
        return lastCheckedAt;
    }

    public LocalDate getAsOf() {
        return asOf;
    }
}
