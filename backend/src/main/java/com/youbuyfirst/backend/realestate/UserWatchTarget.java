package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "user_watch_targets")
public class UserWatchTarget {

    @Id
    @Column(length = 36)
    private String id;

    @Column(name = "user_id", nullable = false, length = 36)
    private String userId;

    @Column(name = "target_type", nullable = false, length = 30)
    private String targetType;

    @Column(name = "target_id", nullable = false, length = 160)
    private String targetId;

    @Column(name = "display_name", nullable = false, length = 120)
    private String displayName;

    @Column(name = "landing_path", nullable = false, length = 600)
    private String landingPath;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected UserWatchTarget() {
    }

    private UserWatchTarget(
            String id,
            String userId,
            String targetType,
            String targetId,
            String displayName,
            String landingPath,
            Instant now
    ) {
        this.id = id;
        this.userId = userId;
        this.targetType = targetType;
        this.targetId = targetId;
        this.displayName = displayName;
        this.landingPath = landingPath;
        this.createdAt = now;
        this.updatedAt = now;
    }

    public static UserWatchTarget create(
            String userId,
            String targetType,
            String targetId,
            String displayName,
            String landingPath,
            Instant now
    ) {
        return new UserWatchTarget(
                UUID.randomUUID().toString(),
                userId,
                targetType,
                targetId,
                displayName,
                landingPath,
                now
        );
    }

    public void update(String displayName, String landingPath, Instant now) {
        this.displayName = displayName;
        this.landingPath = landingPath;
        this.updatedAt = now;
    }

    public String getId() {
        return id;
    }

    public String getUserId() {
        return userId;
    }

    public String getTargetType() {
        return targetType;
    }

    public String getTargetId() {
        return targetId;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getLandingPath() {
        return landingPath;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }
}
