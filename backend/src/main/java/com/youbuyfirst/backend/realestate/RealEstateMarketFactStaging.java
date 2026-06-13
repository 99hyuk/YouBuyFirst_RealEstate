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
        name = "real_estate_market_fact_staging",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_real_estate_market_fact_staging_raw_item",
                columnNames = "raw_item_id"
        )
)
public class RealEstateMarketFactStaging {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "raw_item_id", nullable = false)
    private Long rawItemId;

    @Column(name = "provider_dataset", nullable = false, length = 100)
    private String providerDataset;

    @Column(name = "provider_object_id", nullable = false, length = 240)
    private String providerObjectId;

    @Column(name = "target_type", nullable = false, length = 30)
    private String targetType;

    @Column(name = "target_id", length = 120)
    private String targetId;

    @Column(name = "legal_dong_code", length = 20)
    private String legalDongCode;

    @Column(name = "fact_type", nullable = false, length = 60)
    private String factType;

    @Column(name = "observed_at")
    private LocalDate observedAt;

    @Column(name = "as_of", nullable = false)
    private LocalDate asOf;

    @Column(name = "value_json", nullable = false, columnDefinition = "text")
    private String valueJson;

    @Column(name = "validation_status", nullable = false, length = 30)
    private String validationStatus;

    @Column(name = "validation_message", columnDefinition = "text")
    private String validationMessage;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected RealEstateMarketFactStaging() {
    }

    public RealEstateMarketFactStaging(Long rawItemId) {
        this.rawItemId = rawItemId;
    }

    public void update(
            String providerDataset,
            String providerObjectId,
            String targetType,
            String targetId,
            String legalDongCode,
            String factType,
            LocalDate observedAt,
            LocalDate asOf,
            String valueJson,
            String validationStatus,
            String validationMessage,
            Instant now
    ) {
        this.providerDataset = providerDataset;
        this.providerObjectId = providerObjectId;
        this.targetType = targetType;
        this.targetId = targetId;
        this.legalDongCode = legalDongCode;
        this.factType = factType;
        this.observedAt = observedAt;
        this.asOf = asOf;
        this.valueJson = valueJson;
        this.validationStatus = validationStatus;
        this.validationMessage = validationMessage;
        if (this.createdAt == null) {
            this.createdAt = now;
        }
    }

    public Long getRawItemId() {
        return rawItemId;
    }

    public String getProviderDataset() {
        return providerDataset;
    }

    public String getProviderObjectId() {
        return providerObjectId;
    }

    public String getTargetType() {
        return targetType;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getLegalDongCode() {
        return legalDongCode;
    }

    public String getFactType() {
        return factType;
    }

    public LocalDate getObservedAt() {
        return observedAt;
    }

    public LocalDate getAsOf() {
        return asOf;
    }

    public String getValueJson() {
        return valueJson;
    }

    public String getValidationStatus() {
        return validationStatus;
    }
}
