package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.Locale;

@Entity
@Table(name = "real_estate_targets")
public class RealEstateTarget {

    @Id
    @Column(length = 120)
    private String id;

    @Column(name = "target_type", nullable = false, length = 30)
    private String targetType;

    @Column(name = "display_name", nullable = false, length = 120)
    private String displayName;

    @Column(nullable = false, length = 160)
    private String slug;

    @Column(name = "normalized_name", nullable = false, length = 160)
    private String normalizedName;

    @Column(name = "review_state", nullable = false, length = 30)
    private String reviewState;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstateTarget() {
    }

    public RealEstateTarget(
            String id,
            String targetType,
            String displayName,
            String slug,
            String reviewState,
            String dataStatus,
            Instant now
    ) {
        this.id = id;
        this.createdAt = now;
        update(targetType, displayName, slug, reviewState, dataStatus, now);
    }

    public void update(
            String targetType,
            String displayName,
            String slug,
            String reviewState,
            String dataStatus,
            Instant now
    ) {
        this.targetType = targetType;
        this.displayName = displayName;
        this.slug = slug;
        this.normalizedName = normalizeName(displayName);
        this.reviewState = reviewState;
        this.dataStatus = dataStatus;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getTargetType() {
        return targetType;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getSlug() {
        return slug;
    }

    public String getNormalizedName() {
        return normalizedName;
    }

    public String getReviewState() {
        return reviewState;
    }

    public String getDataStatus() {
        return dataStatus;
    }

    private static String normalizeName(String value) {
        if (value == null) {
            return "";
        }
        return value.toLowerCase(Locale.ROOT).replace(" ", "");
    }
}
