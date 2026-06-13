package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;

import java.time.Instant;

@Entity
@Table(name = "policy_event_targets")
@IdClass(PolicyEventTargetId.class)
public class PolicyEventTarget {

    @Id
    @Column(name = "policy_event_id", nullable = false, length = 120)
    private String policyEventId;

    @Id
    @Column(name = "target_id", nullable = false, length = 120)
    private String targetId;

    @Id
    @Column(name = "impact_type", nullable = false, length = 40)
    private String impactType;

    @Column(nullable = false)
    private Double confidence;

    @Column(name = "review_state", nullable = false, length = 30)
    private String reviewState;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected PolicyEventTarget() {
    }

    public PolicyEventTarget(
            String policyEventId,
            String targetId,
            String impactType,
            Instant now
    ) {
        this.policyEventId = policyEventId;
        this.targetId = targetId;
        this.impactType = impactType;
        this.createdAt = now;
    }

    public void update(Double confidence, String reviewState, Instant now) {
        this.confidence = confidence;
        this.reviewState = reviewState;
        this.updatedAt = now;
    }
}
