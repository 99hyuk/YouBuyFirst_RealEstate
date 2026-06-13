package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;

@Entity
@Table(
        name = "content_items",
        uniqueConstraints = @UniqueConstraint(name = "uk_content_items_url", columnNames = "url")
)
public class RealEstateContentItem {

    @Id
    @Column(length = 120)
    private String id;

    @Column(name = "source_id", length = 120)
    private String sourceId;

    @Column(name = "content_type", nullable = false, length = 40)
    private String contentType;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(columnDefinition = "text")
    private String snippet;

    @Column(nullable = false, length = 1000)
    private String url;

    @Column(length = 160)
    private String domain;

    @Column(name = "published_at")
    private Instant publishedAt;

    @Column(name = "metric_label", length = 120)
    private String metricLabel;

    @Column(name = "status_label", length = 120)
    private String statusLabel;

    @Column(name = "ingested_at", nullable = false)
    private Instant ingestedAt;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateContentItem() {
    }

    public RealEstateContentItem(String id, Instant now) {
        this.id = id;
        this.createdAt = now;
    }

    public void update(
            String sourceId,
            String contentType,
            String title,
            String snippet,
            String url,
            String domain,
            Instant publishedAt,
            String metricLabel,
            String statusLabel,
            Instant ingestedAt,
            String dataStatus,
            Instant now
    ) {
        this.sourceId = sourceId;
        this.contentType = contentType;
        this.title = title;
        this.snippet = snippet;
        this.url = url;
        this.domain = domain;
        this.publishedAt = publishedAt;
        this.metricLabel = metricLabel;
        this.statusLabel = statusLabel;
        this.ingestedAt = ingestedAt;
        this.dataStatus = dataStatus;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getSourceId() {
        return sourceId;
    }

    public String getContentType() {
        return contentType;
    }

    public String getTitle() {
        return title;
    }

    public String getSnippet() {
        return snippet;
    }

    public String getUrl() {
        return url;
    }

    public String getDomain() {
        return domain;
    }

    public Instant getPublishedAt() {
        return publishedAt;
    }

    public String getMetricLabel() {
        return metricLabel;
    }

    public String getStatusLabel() {
        return statusLabel;
    }

    public Instant getIngestedAt() {
        return ingestedAt;
    }

    public String getDataStatus() {
        return dataStatus;
    }
}
