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
import java.util.Locale;

@Entity
@Table(
        name = "real_estate_aliases",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_real_estate_alias_target_normalized",
                columnNames = {"target_id", "normalized_alias"}
        )
)
public class RealEstateAlias {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "target_id", nullable = false, length = 120)
    private String targetId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "target_id", insertable = false, updatable = false)
    private RealEstateTarget target;

    @Column(name = "target_type", nullable = false, length = 30)
    private String targetType;

    @Column(nullable = false, length = 200)
    private String alias;

    @Column(name = "normalized_alias", nullable = false, length = 200)
    private String normalizedAlias;

    @Column(name = "alias_type", nullable = false, length = 40)
    private String aliasType;

    @Column(nullable = false, length = 120)
    private String source;

    @Column(name = "evidence_url", length = 1000)
    private String evidenceUrl;

    @Column(nullable = false)
    private Double confidence;

    @Column(name = "review_state", nullable = false, length = 30)
    private String reviewState;

    @Column(nullable = false)
    private Boolean ambiguous;

    @Column(name = "created_by", nullable = false, length = 80)
    private String createdBy;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateAlias() {
    }

    public RealEstateAlias(
            String targetId,
            String targetType,
            String alias,
            String aliasType,
            String source,
            String evidenceUrl,
            Double confidence,
            String reviewState,
            Boolean ambiguous,
            String createdBy,
            Instant now
    ) {
        this.targetId = targetId;
        this.createdAt = now;
        update(targetType, alias, aliasType, source, evidenceUrl, confidence, reviewState, ambiguous, createdBy, now);
    }

    public void update(
            String targetType,
            String alias,
            String aliasType,
            String source,
            String evidenceUrl,
            Double confidence,
            String reviewState,
            Boolean ambiguous,
            String createdBy,
            Instant now
    ) {
        this.targetType = targetType;
        this.alias = alias;
        this.normalizedAlias = normalizeAlias(alias);
        this.aliasType = aliasType;
        this.source = source;
        this.evidenceUrl = evidenceUrl;
        this.confidence = confidence;
        this.reviewState = reviewState;
        this.ambiguous = ambiguous;
        this.createdBy = createdBy;
        this.updatedAt = now;
    }

    public Long getId() {
        return id;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getTargetType() {
        return targetType;
    }

    public String getAlias() {
        return alias;
    }

    public String getNormalizedAlias() {
        return normalizedAlias;
    }

    public String getAliasType() {
        return aliasType;
    }

    public String getSource() {
        return source;
    }

    public String getEvidenceUrl() {
        return evidenceUrl;
    }

    public Double getConfidence() {
        return confidence;
    }

    public String getReviewState() {
        return reviewState;
    }

    public Boolean getAmbiguous() {
        return ambiguous;
    }

    public String getCreatedBy() {
        return createdBy;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public static String normalizeAlias(String value) {
        if (value == null) {
            return "";
        }
        String lowerCased = value.trim().toLowerCase(Locale.ROOT);
        StringBuilder normalized = new StringBuilder();
        lowerCased.codePoints()
                .filter(Character::isLetterOrDigit)
                .forEach(normalized::appendCodePoint);
        return normalized.toString();
    }
}
