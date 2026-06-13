package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "map_layer_snapshots")
public class MapLayerSnapshot {

    @Id
    @Column(length = 180)
    private String id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "target_id", insertable = false, updatable = false)
    private RealEstateTarget target;

    @Column(name = "target_id", nullable = false, length = 120)
    private String targetId;

    @Column(name = "layer_type", nullable = false, length = 30)
    private String layerType;

    @Column(name = "period_key", nullable = false, length = 30)
    private String periodKey;

    @Column(name = "change_pct", nullable = false, precision = 12, scale = 4)
    private BigDecimal changePct;

    @Column(name = "sample_count", nullable = false)
    private int sampleCount;

    @Column(nullable = false, precision = 12, scale = 4)
    private BigDecimal confidence;

    @Column(name = "as_of", nullable = false)
    private Instant asOf;

    @Column(nullable = false, length = 60)
    private String provider;

    @Column(name = "source_label", nullable = false, length = 160)
    private String sourceLabel;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(nullable = false)
    private boolean stale;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected MapLayerSnapshot() {
    }

    public String getId() {
        return id;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getLayerType() {
        return layerType;
    }

    public String getPeriodKey() {
        return periodKey;
    }

    public BigDecimal getChangePct() {
        return changePct;
    }

    public int getSampleCount() {
        return sampleCount;
    }

    public BigDecimal getConfidence() {
        return confidence;
    }

    public Instant getAsOf() {
        return asOf;
    }

    public String getProvider() {
        return provider;
    }

    public String getSourceLabel() {
        return sourceLabel;
    }

    public String getDataStatus() {
        return dataStatus;
    }

    public boolean isStale() {
        return stale;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
