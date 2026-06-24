package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "market_data_sources")
public class MarketDataSource {

    @Id
    @Column(length = 80)
    private String id;

    @Column(nullable = false, length = 120)
    private String title;

    @Column(nullable = false, length = 120)
    private String label;

    @Column(nullable = false, length = 80)
    private String provider;

    @Column(name = "source_url", nullable = false, length = 1000)
    private String sourceUrl;

    @Column(nullable = false, length = 40)
    private String category;

    @Column(nullable = false, length = 40)
    private String tone;

    @Column(nullable = false)
    private boolean enabled;

    @Column(name = "last_checked_at")
    private Instant lastCheckedAt;

    @Column(nullable = false)
    private boolean stale;

    @Column(nullable = false, length = 40)
    private String status;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected MarketDataSource() {
    }

    public MarketDataSource(String id, Instant now) {
        this.id = id;
        this.createdAt = now;
    }

    public void update(
            String title,
            String label,
            String provider,
            String sourceUrl,
            String category,
            String tone,
            boolean enabled,
            Instant lastCheckedAt,
            boolean stale,
            String status,
            Instant now
    ) {
        this.title = title;
        this.label = label;
        this.provider = provider;
        this.sourceUrl = sourceUrl;
        this.category = category;
        this.tone = tone;
        this.enabled = enabled;
        this.lastCheckedAt = lastCheckedAt;
        this.stale = stale;
        this.status = status;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public String getLabel() {
        return label;
    }

    public String getProvider() {
        return provider;
    }

    public String getSourceUrl() {
        return sourceUrl;
    }

    public String getCategory() {
        return category;
    }

    public String getTone() {
        return tone;
    }

    public boolean isEnabled() {
        return enabled;
    }

    public Instant getLastCheckedAt() {
        return lastCheckedAt;
    }

    public boolean isStale() {
        return stale;
    }

    public String getStatus() {
        return status;
    }
}
