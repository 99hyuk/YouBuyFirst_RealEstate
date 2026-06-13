package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;

@Entity
@Table(
        name = "real_estate_target_edges",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_real_estate_target_edges",
                columnNames = {"from_target_id", "to_target_id", "edge_type"}
        )
)
public class RealEstateTargetEdge {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "from_target_id", nullable = false, length = 120)
    private String fromTargetId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "from_target_id", insertable = false, updatable = false)
    private RealEstateTarget fromTarget;

    @Column(name = "from_target_type", nullable = false, length = 30)
    private String fromTargetType;

    @Column(name = "to_target_id", nullable = false, length = 120)
    private String toTargetId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "to_target_id", insertable = false, updatable = false)
    private RealEstateTarget toTarget;

    @Column(name = "to_target_type", nullable = false, length = 30)
    private String toTargetType;

    @Column(name = "edge_type", nullable = false, length = 40)
    private String edgeType;

    @Column(nullable = false)
    private Double confidence;

    @Column(nullable = false, length = 120)
    private String source;

    @Column(name = "review_state", nullable = false, length = 30)
    private String reviewState;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateTargetEdge() {
    }

    public RealEstateTargetEdge(
            String fromTargetId,
            String fromTargetType,
            String toTargetId,
            String toTargetType,
            String edgeType,
            Double confidence,
            String source,
            String reviewState,
            Instant now
    ) {
        this.fromTargetId = fromTargetId;
        this.toTargetId = toTargetId;
        this.createdAt = now;
        update(fromTargetType, toTargetType, edgeType, confidence, source, reviewState, now);
    }

    public void update(
            String fromTargetType,
            String toTargetType,
            String edgeType,
            Double confidence,
            String source,
            String reviewState,
            Instant now
    ) {
        this.fromTargetType = fromTargetType;
        this.toTargetType = toTargetType;
        this.edgeType = edgeType;
        this.confidence = confidence;
        this.source = source;
        this.reviewState = reviewState;
        this.updatedAt = now;
    }

    public Long getId() {
        return id;
    }

    public String getFromTargetId() {
        return fromTargetId;
    }

    public RealEstateTarget getFromTarget() {
        return fromTarget;
    }

    public String getFromTargetType() {
        return fromTargetType;
    }

    public String getToTargetId() {
        return toTargetId;
    }

    public RealEstateTarget getToTarget() {
        return toTarget;
    }

    public String getToTargetType() {
        return toTargetType;
    }

    public String getEdgeType() {
        return edgeType;
    }

    public Double getConfidence() {
        return confidence;
    }

    public String getSource() {
        return source;
    }

    public String getReviewState() {
        return reviewState;
    }
}
