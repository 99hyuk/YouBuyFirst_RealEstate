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
@Table(name = "real_estate_regional_report_sources")
public class RealEstateRegionalReportSource {

    @Id
    @Column(length = 160)
    private String id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "report_target_id", nullable = false, referencedColumnName = "target_id")
    private RealEstateRegionalReport report;

    @Column(name = "display_order", nullable = false)
    private int displayOrder;

    @Column(name = "ref_type", nullable = false, length = 60)
    private String refType;

    @Column(name = "ref_id", length = 160)
    private String refId;

    @Column(nullable = false, length = 120)
    private String label;

    @Column(nullable = false, length = 240)
    private String title;

    @Column(columnDefinition = "text")
    private String url;

    @Column(name = "source_name", length = 160)
    private String sourceName;

    @Column(name = "published_at")
    private Instant publishedAt;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateRegionalReportSource() {
    }

    public RealEstateRegionalReportSource(
            String id,
            int displayOrder,
            String refType,
            String refId,
            String label,
            String title,
            String url,
            String sourceName,
            Instant publishedAt,
            String dataStatus,
            Instant now
    ) {
        this.id = id;
        this.displayOrder = displayOrder;
        this.refType = refType;
        this.refId = refId;
        this.label = label;
        this.title = title;
        this.url = url;
        this.sourceName = sourceName;
        this.publishedAt = publishedAt;
        this.dataStatus = dataStatus;
        this.createdAt = now;
        this.updatedAt = now;
    }

    void attachTo(RealEstateRegionalReport report) {
        this.report = report;
    }

    public String getId() {
        return id;
    }

    public int getDisplayOrder() {
        return displayOrder;
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

    public String getTitle() {
        return title;
    }

    public String getUrl() {
        return url;
    }

    public String getSourceName() {
        return sourceName;
    }

    public Instant getPublishedAt() {
        return publishedAt;
    }

    public String getDataStatus() {
        return dataStatus;
    }
}
