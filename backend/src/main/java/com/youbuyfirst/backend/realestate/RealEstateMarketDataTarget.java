package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "real_estate_market_data_targets")
public class RealEstateMarketDataTarget {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "target_id", nullable = false, length = 120)
    private String targetId;

    @Column(nullable = false, length = 60)
    private String provider;

    @Column(name = "provider_dataset", nullable = false, length = 80)
    private String providerDataset;

    @Column(name = "lawd_code", nullable = false, length = 20)
    private String lawdCode;

    @Column(nullable = false)
    private boolean enabled;

    @Column(name = "refresh_interval_hours", nullable = false)
    private int refreshIntervalHours;

    @Column(name = "stale_after_hours", nullable = false)
    private int staleAfterHours;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateMarketDataTarget() {
    }

    public RealEstateMarketDataTarget(
            String targetId,
            String provider,
            String providerDataset,
            String lawdCode,
            boolean enabled,
            int refreshIntervalHours,
            int staleAfterHours,
            Instant now
    ) {
        this.targetId = targetId;
        this.provider = provider;
        this.providerDataset = providerDataset;
        this.lawdCode = lawdCode;
        this.createdAt = now;
        update(enabled, refreshIntervalHours, staleAfterHours, now);
    }

    public void update(boolean enabled, int refreshIntervalHours, int staleAfterHours, Instant now) {
        this.enabled = enabled;
        this.refreshIntervalHours = refreshIntervalHours;
        this.staleAfterHours = staleAfterHours;
        this.updatedAt = now;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getProvider() {
        return provider;
    }

    public String getProviderDataset() {
        return providerDataset;
    }

    public String getLawdCode() {
        return lawdCode;
    }

    public boolean isEnabled() {
        return enabled;
    }

    public int getRefreshIntervalHours() {
        return refreshIntervalHours;
    }

    public int getStaleAfterHours() {
        return staleAfterHours;
    }
}
