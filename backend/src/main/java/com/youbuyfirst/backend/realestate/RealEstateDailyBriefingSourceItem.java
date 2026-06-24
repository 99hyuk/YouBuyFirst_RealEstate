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
@Table(name = "daily_briefing_source_items")
public class RealEstateDailyBriefingSourceItem {

    @Id
    @Column(length = 160)
    private String id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "briefing_id", nullable = false)
    private RealEstateDailyBriefing briefing;

    @Column(name = "source_type", nullable = false, length = 40)
    private String sourceType;

    @Column(name = "ref_id", length = 160)
    private String refId;

    @Column(length = 160)
    private String label;

    @Column(nullable = false, length = 300)
    private String title;

    @Column(length = 1000)
    private String url;

    @Column(name = "display_order", nullable = false)
    private int displayOrder;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateDailyBriefingSourceItem() {
    }

    public RealEstateDailyBriefingSourceItem(
            String id,
            String sourceType,
            String refId,
            String label,
            String title,
            String url,
            int displayOrder,
            Instant now
    ) {
        this.id = id;
        this.sourceType = sourceType;
        this.refId = refId;
        this.label = label;
        this.title = title;
        this.url = url;
        this.displayOrder = displayOrder;
        this.createdAt = now;
        this.updatedAt = now;
    }

    void attachTo(RealEstateDailyBriefing briefing) {
        this.briefing = briefing;
    }

    public String getId() {
        return id;
    }

    public String getSourceType() {
        return sourceType;
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

    public int getDisplayOrder() {
        return displayOrder;
    }
}
