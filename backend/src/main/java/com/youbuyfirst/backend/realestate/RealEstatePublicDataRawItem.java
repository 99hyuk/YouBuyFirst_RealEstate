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
        name = "real_estate_public_data_raw_items",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_real_estate_public_data_raw_items_provider_object",
                columnNames = {"provider_dataset", "provider_object_id"}
        )
)
public class RealEstatePublicDataRawItem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "import_run_id", nullable = false)
    private Long importRunId;

    @Column(name = "provider_dataset", nullable = false, length = 100)
    private String providerDataset;

    @Column(name = "provider_object_id", nullable = false, length = 240)
    private String providerObjectId;

    @Column(name = "legal_dong_code", length = 20)
    private String legalDongCode;

    @Column(name = "target_id", length = 120)
    private String targetId;

    @Column(name = "observed_at")
    private LocalDate observedAt;

    @Column(name = "as_of", nullable = false)
    private LocalDate asOf;

    @Column(name = "source_updated_at")
    private Instant sourceUpdatedAt;

    @Column(name = "payload_hash", nullable = false, length = 64)
    private String payloadHash;

    @Column(name = "raw_payload_json", nullable = false, columnDefinition = "text")
    private String rawPayloadJson;

    @Column(name = "landing_status", nullable = false, length = 30)
    private String landingStatus;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    protected RealEstatePublicDataRawItem() {
    }

    public RealEstatePublicDataRawItem(String providerDataset, String providerObjectId) {
        this.providerDataset = providerDataset;
        this.providerObjectId = providerObjectId;
    }

    public void update(
            Long importRunId,
            String legalDongCode,
            String targetId,
            LocalDate observedAt,
            LocalDate asOf,
            Instant sourceUpdatedAt,
            String payloadHash,
            String rawPayloadJson,
            String landingStatus,
            Instant now
    ) {
        this.importRunId = importRunId;
        this.legalDongCode = legalDongCode;
        this.targetId = targetId;
        this.observedAt = observedAt;
        this.asOf = asOf;
        this.sourceUpdatedAt = sourceUpdatedAt;
        this.payloadHash = payloadHash;
        this.rawPayloadJson = rawPayloadJson;
        this.landingStatus = landingStatus;
        if (this.createdAt == null) {
            this.createdAt = now;
        }
    }

    public Long getId() {
        return id;
    }
}
