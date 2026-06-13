package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@IdClass(RealEstateContentTargetLinkId.class)
@Table(name = "content_target_links")
public class RealEstateContentTargetLink {

    @Id
    @Column(name = "content_item_id", length = 120)
    private String contentItemId;

    @Id
    @Column(name = "target_id", length = 120)
    private String targetId;

    @Id
    @Column(name = "link_type", length = 40)
    private String linkType;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "content_item_id", insertable = false, updatable = false)
    private RealEstateContentItem contentItem;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "target_id", insertable = false, updatable = false)
    private RealEstateTarget target;

    @Column(nullable = false)
    private double confidence;

    @Column(name = "review_state", nullable = false, length = 30)
    private String reviewState;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateContentTargetLink() {
    }

    public RealEstateContentTargetLink(
            RealEstateContentItem contentItem,
            RealEstateTarget target,
            String linkType,
            Instant now
    ) {
        this.contentItem = contentItem;
        this.contentItemId = contentItem.getId();
        this.target = target;
        this.targetId = target.getId();
        this.linkType = linkType;
        this.createdAt = now;
    }

    public void update(double confidence, String reviewState, Instant now) {
        this.confidence = confidence;
        this.reviewState = reviewState;
        this.updatedAt = now;
    }

    public String getContentItemId() {
        return contentItemId;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getLinkType() {
        return linkType;
    }

    public RealEstateContentItem getContentItem() {
        return contentItem;
    }

    public RealEstateTarget getTarget() {
        return target;
    }

    public double getConfidence() {
        return confidence;
    }

    public String getReviewState() {
        return reviewState;
    }
}
