package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(
        name = "real_estate_market_facts",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_real_estate_market_facts_provider_object",
                columnNames = {"provider", "provider_dataset", "provider_object_id"}
        )
)
public class RealEstateMarketFact {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "target_type", nullable = false, length = 30)
    private String targetType;

    @Column(name = "target_id", length = 120)
    private String targetId;

    @Column(name = "fact_type", nullable = false, length = 40)
    private String factType;

    @Column(nullable = false, length = 60)
    private String provider;

    @Column(name = "provider_dataset", nullable = false, length = 80)
    private String providerDataset;

    @Column(name = "provider_object_id", nullable = false, length = 180)
    private String providerObjectId;

    @Column(name = "legal_dong_code", nullable = false, length = 20)
    private String legalDongCode;

    @Column(name = "observed_at", nullable = false)
    private LocalDate observedAt;

    @Column(name = "as_of", nullable = false)
    private LocalDate asOf;

    @Column(name = "ingested_at", nullable = false)
    private Instant ingestedAt;

    @Column(name = "source_updated_at")
    private Instant sourceUpdatedAt;

    @Column(name = "value_json", nullable = false, columnDefinition = "text")
    private String valueJson;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(nullable = false)
    private boolean stale;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateMarketFact() {
    }

    public RealEstateMarketFact(String provider, String providerDataset, String providerObjectId) {
        this.provider = provider;
        this.providerDataset = providerDataset;
        this.providerObjectId = providerObjectId;
    }

    public void update(
            String targetType,
            String targetId,
            String factType,
            String legalDongCode,
            LocalDate observedAt,
            LocalDate asOf,
            Instant ingestedAt,
            Instant sourceUpdatedAt,
            String valueJson,
            String dataStatus,
            boolean stale,
            Instant now
    ) {
        this.targetType = targetType;
        this.targetId = targetId;
        this.factType = factType;
        this.legalDongCode = legalDongCode;
        this.observedAt = observedAt;
        this.asOf = asOf;
        this.ingestedAt = ingestedAt;
        this.sourceUpdatedAt = sourceUpdatedAt;
        this.valueJson = valueJson;
        this.dataStatus = dataStatus;
        this.stale = stale;
        if (this.createdAt == null) {
            this.createdAt = now;
        }
        this.updatedAt = now;
    }

    public String getTargetType() {
        return targetType;
    }

    public Long getId() {
        return id;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getFactType() {
        return factType;
    }

    public String getProvider() {
        return provider;
    }

    public String getProviderDataset() {
        return providerDataset;
    }

    public String getProviderObjectId() {
        return providerObjectId;
    }

    public String getLegalDongCode() {
        return legalDongCode;
    }

    public LocalDate getObservedAt() {
        return observedAt;
    }

    public LocalDate getAsOf() {
        return asOf;
    }

    public Instant getIngestedAt() {
        return ingestedAt;
    }

    public Instant getSourceUpdatedAt() {
        return sourceUpdatedAt;
    }

    public String getValueJson() {
        return valueJson;
    }

    public String getDataStatus() {
        return dataStatus;
    }

    public boolean isStale() {
        return stale;
    }
}
