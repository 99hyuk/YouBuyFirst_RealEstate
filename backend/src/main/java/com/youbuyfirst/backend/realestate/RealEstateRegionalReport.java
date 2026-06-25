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
@Table(name = "real_estate_regional_reports")
public class RealEstateRegionalReport {

    @Id
    @Column(name = "target_id", length = 120)
    private String targetId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "target_id", insertable = false, updatable = false)
    private RealEstateTarget target;

    @Column(name = "report_id", nullable = false, length = 160)
    private String reportId;

    @Column(name = "report_version", nullable = false, length = 80)
    private String reportVersion;

    @Column(name = "prompt_version", length = 80)
    private String promptVersion;

    @Column(name = "model_name", length = 80)
    private String modelName;

    @Column(name = "generated_by", nullable = false, length = 80)
    private String generatedBy;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(nullable = false, length = 300)
    private String headline;

    @Column(nullable = false, columnDefinition = "text")
    private String summary;

    @Column(nullable = false, columnDefinition = "text")
    private String body;

    @Column(name = "expectation_points_json", nullable = false, columnDefinition = "text")
    private String expectationPointsJson;

    @Column(name = "concern_points_json", nullable = false, columnDefinition = "text")
    private String concernPointsJson;

    @Column(name = "data_quality", nullable = false, length = 30)
    private String dataQuality;

    @Column
    private Double confidence;

    @Column(name = "as_of", nullable = false)
    private Instant asOf;

    @Column(name = "published_at", nullable = false)
    private Instant publishedAt;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @OrderBy("displayOrder asc, id asc")
    @OneToMany(mappedBy = "report", cascade = CascadeType.ALL, orphanRemoval = true)
    private final List<RealEstateRegionalReportSource> sources = new ArrayList<>();

    protected RealEstateRegionalReport() {
    }

    public RealEstateRegionalReport(String targetId, Instant now) {
        this.targetId = targetId;
        this.createdAt = now;
    }

    public void update(
            RealEstateTarget target,
            String reportId,
            String reportVersion,
            String promptVersion,
            String modelName,
            String generatedBy,
            String title,
            String headline,
            String summary,
            String body,
            String expectationPointsJson,
            String concernPointsJson,
            String dataQuality,
            Double confidence,
            Instant asOf,
            Instant publishedAt,
            List<RealEstateRegionalReportSource> nextSources,
            Instant now
    ) {
        this.targetId = target.getId();
        this.target = target;
        this.reportId = reportId;
        this.reportVersion = reportVersion;
        this.promptVersion = promptVersion;
        this.modelName = modelName;
        this.generatedBy = generatedBy;
        this.title = title;
        this.headline = headline;
        this.summary = summary;
        this.body = body;
        this.expectationPointsJson = expectationPointsJson;
        this.concernPointsJson = concernPointsJson;
        this.dataQuality = dataQuality;
        this.confidence = confidence;
        this.asOf = asOf;
        this.publishedAt = publishedAt;
        this.sources.clear();
        nextSources.forEach(this::addSource);
        this.updatedAt = now;
    }

    private void addSource(RealEstateRegionalReportSource source) {
        source.attachTo(this);
        this.sources.add(source);
    }

    public String getTargetId() {
        return targetId;
    }

    public RealEstateTarget getTarget() {
        return target;
    }

    public String getReportId() {
        return reportId;
    }

    public String getReportVersion() {
        return reportVersion;
    }

    public String getPromptVersion() {
        return promptVersion;
    }

    public String getModelName() {
        return modelName;
    }

    public String getGeneratedBy() {
        return generatedBy;
    }

    public String getTitle() {
        return title;
    }

    public String getHeadline() {
        return headline;
    }

    public String getSummary() {
        return summary;
    }

    public String getBody() {
        return body;
    }

    public String getExpectationPointsJson() {
        return expectationPointsJson;
    }

    public String getConcernPointsJson() {
        return concernPointsJson;
    }

    public String getDataQuality() {
        return dataQuality;
    }

    public Double getConfidence() {
        return confidence;
    }

    public Instant getAsOf() {
        return asOf;
    }

    public Instant getPublishedAt() {
        return publishedAt;
    }

    public List<RealEstateRegionalReportSource> getSources() {
        return sources;
    }
}
