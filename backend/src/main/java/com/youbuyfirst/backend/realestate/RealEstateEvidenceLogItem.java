package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "evidence_log_items")
public class RealEstateEvidenceLogItem {

    @Id
    @Column(length = 120)
    private String id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "evidence_log_id", nullable = false)
    private RealEstateEvidenceLog evidenceLog;

    @Column(name = "evidence_type", nullable = false, length = 40)
    private String evidenceType;

    @Column(name = "ref_type", nullable = false, length = 60)
    private String refType;

    @Column(name = "ref_id", nullable = false, length = 120)
    private String refId;

    @Column(nullable = false, length = 160)
    private String label;

    @Column(name = "value_text", length = 500)
    private String valueText;

    @Column(length = 40)
    private String severity;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateEvidenceLogItem() {
    }

    public RealEstateEvidenceLogItem(
            String id,
            String evidenceType,
            String refType,
            String refId,
            String label,
            String valueText,
            String severity,
            Instant now
    ) {
        this.id = id;
        this.evidenceType = evidenceType;
        this.refType = refType;
        this.refId = refId;
        this.label = label;
        this.valueText = valueText;
        this.severity = severity;
        this.createdAt = now;
        this.updatedAt = now;
    }

    void attachTo(RealEstateEvidenceLog evidenceLog) {
        this.evidenceLog = evidenceLog;
    }

    public String getId() {
        return id;
    }

    public String getEvidenceType() {
        return evidenceType;
    }

    public String getRefType() {
        return refType;
    }

    public String getRefId() {
        return refId;
    }

    public String getLabel() {
        return label;
    }

    public String getValueText() {
        return valueText;
    }

    public String getSeverity() {
        return severity;
    }
}
