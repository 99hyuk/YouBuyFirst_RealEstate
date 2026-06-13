package com.youbuyfirst.backend.realestate;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "evidence_logs")
public class RealEstateEvidenceLog {

    @Id
    @Column(length = 120)
    private String id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "target_id", nullable = false)
    private RealEstateTarget target;

    @Column(name = "snapshot_id")
    private Long snapshotId;

    @Column(name = "evaluation_version", nullable = false, length = 80)
    private String evaluationVersion;

    @Column(name = "prompt_version", length = 80)
    private String promptVersion;

    @Column(name = "model_name", length = 80)
    private String modelName;

    @Column(nullable = false, length = 40)
    private String tone;

    @Column(nullable = false, columnDefinition = "text")
    private String summary;

    @Column(columnDefinition = "text")
    private String subtitle;

    @Column(name = "caveats_json", nullable = false, columnDefinition = "text")
    private String caveatsJson;

    @Column(name = "data_quality", nullable = false, length = 30)
    private String dataQuality;

    @Column
    private Double confidence;

    @Column(name = "skip_reason", length = 500)
    private String skipReason;

    @Column(name = "evaluated_at", nullable = false)
    private Instant evaluatedAt;

    @Column(name = "as_of", nullable = false)
    private Instant asOf;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @OrderBy("createdAt asc, id asc")
    @OneToMany(mappedBy = "evidenceLog", cascade = CascadeType.ALL, orphanRemoval = true)
    private final List<RealEstateEvidenceLogItem> items = new ArrayList<>();

    protected RealEstateEvidenceLog() {
    }

    public RealEstateEvidenceLog(String id, Instant now) {
        this.id = id;
        this.createdAt = now;
    }

    public void update(
            RealEstateTarget target,
            Long snapshotId,
            String evaluationVersion,
            String promptVersion,
            String modelName,
            String tone,
            String summary,
            String subtitle,
            String caveatsJson,
            String dataQuality,
            Double confidence,
            String skipReason,
            Instant evaluatedAt,
            Instant asOf,
            List<RealEstateEvidenceLogItem> nextItems,
            Instant now
    ) {
        this.target = target;
        this.snapshotId = snapshotId;
        this.evaluationVersion = evaluationVersion;
        this.promptVersion = promptVersion;
        this.modelName = modelName;
        this.tone = tone;
        this.summary = summary;
        this.subtitle = subtitle;
        this.caveatsJson = caveatsJson;
        this.dataQuality = dataQuality;
        this.confidence = confidence;
        this.skipReason = skipReason;
        this.evaluatedAt = evaluatedAt;
        this.asOf = asOf;
        this.items.clear();
        nextItems.forEach(this::addItem);
        this.updatedAt = now;
    }

    private void addItem(RealEstateEvidenceLogItem item) {
        item.attachTo(this);
        this.items.add(item);
    }

    public String getId() {
        return id;
    }

    public RealEstateTarget getTarget() {
        return target;
    }

    public Long getSnapshotId() {
        return snapshotId;
    }

    public String getEvaluationVersion() {
        return evaluationVersion;
    }

    public String getPromptVersion() {
        return promptVersion;
    }

    public String getModelName() {
        return modelName;
    }

    public String getTone() {
        return tone;
    }

    public String getSummary() {
        return summary;
    }

    public String getSubtitle() {
        return subtitle;
    }

    public String getCaveatsJson() {
        return caveatsJson;
    }

    public String getDataQuality() {
        return dataQuality;
    }

    public Double getConfidence() {
        return confidence;
    }

    public String getSkipReason() {
        return skipReason;
    }

    public Instant getEvaluatedAt() {
        return evaluatedAt;
    }

    public Instant getAsOf() {
        return asOf;
    }

    public List<RealEstateEvidenceLogItem> getItems() {
        return items;
    }
}
