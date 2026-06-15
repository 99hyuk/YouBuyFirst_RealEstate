package com.youbuyfirst.backend.indicator;

import com.youbuyfirst.backend.realestate.RealEstateTarget;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Entity
@Table(
        name = "real_estate_reaction_snapshots",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_real_estate_reaction_snapshots_target_window",
                columnNames = {"target_id", "window_start", "window_end"}
        )
)
public class RealEstateReactionSnapshot {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "target_type", nullable = false, length = 30)
    private String targetType;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "target_id", nullable = false)
    private RealEstateTarget target;

    @Column(name = "window_start", nullable = false)
    private Instant windowStart;

    @Column(name = "window_end", nullable = false)
    private Instant windowEnd;

    @Column(name = "as_of", nullable = false)
    private Instant asOf;

    @Column(name = "mention_count", nullable = false)
    private int mentionCount;

    @Column(name = "previous_mention_count", nullable = false)
    private int previousMentionCount;

    @Column(name = "expectation_score", nullable = false)
    private double expectationScore;

    @Column(name = "concern_score", nullable = false)
    private double concernScore;

    @Column(name = "neutral_score", nullable = false)
    private double neutralScore;

    @Column(name = "heat_score", nullable = false)
    private int heatScore;

    @Column(nullable = false)
    private double confidence;

    @Column(name = "source_count", nullable = false)
    private int sourceCount;

    @Column(name = "source_skew", nullable = false)
    private double sourceSkew;

    @Column(name = "coverage_status", nullable = false, length = 30)
    private String coverageStatus;

    @Column(nullable = false)
    private boolean stale;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @OrderBy("share desc, label asc")
    @OneToMany(mappedBy = "snapshot", cascade = CascadeType.ALL, orphanRemoval = true)
    private final List<RealEstateReactionSnapshotIssue> issues = new ArrayList<>();

    protected RealEstateReactionSnapshot() {
    }

    public RealEstateReactionSnapshot(RealEstateTarget target, Instant windowStart, Instant windowEnd) {
        this.target = target;
        this.windowStart = windowStart;
        this.windowEnd = windowEnd;
    }

    public void update(
            String targetType,
            RealEstateTarget target,
            Instant asOf,
            int mentionCount,
            int previousMentionCount,
            double expectationScore,
            double concernScore,
            double neutralScore,
            int heatScore,
            double confidence,
            int sourceCount,
            double sourceSkew,
            String coverageStatus,
            boolean stale,
            List<RealEstateReactionSnapshotIssue> nextIssues,
            Instant now
    ) {
        this.targetType = targetType;
        this.target = target;
        this.asOf = asOf;
        this.mentionCount = mentionCount;
        this.previousMentionCount = previousMentionCount;
        this.expectationScore = expectationScore;
        this.concernScore = concernScore;
        this.neutralScore = neutralScore;
        this.heatScore = heatScore;
        this.confidence = confidence;
        this.sourceCount = sourceCount;
        this.sourceSkew = sourceSkew;
        this.coverageStatus = coverageStatus;
        this.stale = stale;
        replaceIssues(nextIssues);
        if (this.createdAt == null) {
            this.createdAt = now;
        }
        this.updatedAt = now;
    }

    private void addIssue(RealEstateReactionSnapshotIssue issue) {
        issue.attachTo(this);
        this.issues.add(issue);
    }

    private void replaceIssues(List<RealEstateReactionSnapshotIssue> nextIssues) {
        Map<String, RealEstateReactionSnapshotIssue> existingByKey = new LinkedHashMap<>();
        for (RealEstateReactionSnapshotIssue issue : issues) {
            existingByKey.put(issue.getIssueKey(), issue);
        }
        List<String> nextIssueKeys = new ArrayList<>();
        for (RealEstateReactionSnapshotIssue nextIssue : nextIssues) {
            RealEstateReactionSnapshotIssue existing = existingByKey.get(nextIssue.getIssueKey());
            if (existing == null) {
                addIssue(nextIssue);
            } else {
                existing.updateFrom(nextIssue);
            }
            nextIssueKeys.add(nextIssue.getIssueKey());
        }
        issues.removeIf(issue -> !nextIssueKeys.contains(issue.getIssueKey()));
    }

    public Long getId() {
        return id;
    }

    public String getTargetType() {
        return targetType;
    }

    public RealEstateTarget getTarget() {
        return target;
    }

    public Instant getWindowStart() {
        return windowStart;
    }

    public Instant getWindowEnd() {
        return windowEnd;
    }

    public Instant getAsOf() {
        return asOf;
    }

    public int getMentionCount() {
        return mentionCount;
    }

    public int getPreviousMentionCount() {
        return previousMentionCount;
    }

    public double getExpectationScore() {
        return expectationScore;
    }

    public double getConcernScore() {
        return concernScore;
    }

    public double getNeutralScore() {
        return neutralScore;
    }

    public int getHeatScore() {
        return heatScore;
    }

    public double getConfidence() {
        return confidence;
    }

    public int getSourceCount() {
        return sourceCount;
    }

    public double getSourceSkew() {
        return sourceSkew;
    }

    public String getCoverageStatus() {
        return coverageStatus;
    }

    public boolean isStale() {
        return stale;
    }

    public List<RealEstateReactionSnapshotIssue> getIssues() {
        return issues;
    }
}
