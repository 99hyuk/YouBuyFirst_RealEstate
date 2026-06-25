package com.youbuyfirst.backend.realestate.dto;

import com.youbuyfirst.backend.realestate.UserWatchTarget;

import java.time.Instant;

public record UserWatchTargetResponse(
        String watchId,
        String targetType,
        String targetId,
        String displayName,
        String landingPath,
        Instant createdAt,
        Instant updatedAt
) {
    public static UserWatchTargetResponse from(UserWatchTarget target) {
        return new UserWatchTargetResponse(
                target.getId(),
                target.getTargetType(),
                target.getTargetId(),
                target.getDisplayName(),
                target.getLandingPath(),
                target.getCreatedAt(),
                target.getUpdatedAt()
        );
    }
}
