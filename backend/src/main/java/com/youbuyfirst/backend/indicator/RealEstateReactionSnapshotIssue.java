package com.youbuyfirst.backend.indicator;

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

@Entity
@Table(
        name = "real_estate_reaction_snapshot_issues",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_real_estate_reaction_snapshot_issues_key",
                columnNames = {"snapshot_id", "issue_key"}
        )
)
public class RealEstateReactionSnapshotIssue {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "snapshot_id", nullable = false)
    private RealEstateReactionSnapshot snapshot;

    @Column(name = "issue_key", nullable = false, length = 80)
    private String issueKey;

    @Column(nullable = false, length = 80)
    private String label;

    @Column(nullable = false)
    private double share;

    @Column(nullable = false, length = 30)
    private String direction;

    @Column(length = 500)
    private String summary;

    @Column(nullable = false)
    private double confidence;

    protected RealEstateReactionSnapshotIssue() {
    }

    public RealEstateReactionSnapshotIssue(
            String issueKey,
            String label,
            double share,
            String direction,
            String summary,
            double confidence
    ) {
        this.issueKey = issueKey;
        this.label = label;
        this.share = share;
        this.direction = direction;
        this.summary = summary;
        this.confidence = confidence;
    }

    void attachTo(RealEstateReactionSnapshot snapshot) {
        this.snapshot = snapshot;
    }

    void updateFrom(RealEstateReactionSnapshotIssue issue) {
        this.label = issue.label;
        this.share = issue.share;
        this.direction = issue.direction;
        this.summary = issue.summary;
        this.confidence = issue.confidence;
    }

    public String getIssueKey() {
        return issueKey;
    }

    public String getLabel() {
        return label;
    }

    public double getShare() {
        return share;
    }

    public String getDirection() {
        return direction;
    }

    public String getSummary() {
        return summary;
    }

    public double getConfidence() {
        return confidence;
    }
}
