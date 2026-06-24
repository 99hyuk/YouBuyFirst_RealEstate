package com.youbuyfirst.backend.auth.dto;

import com.youbuyfirst.backend.auth.AppUser;

import java.time.Instant;

public record CurrentUserResponse(
        String id,
        String username,
        String email,
        String displayName,
        String authProvider,
        Instant createdAt,
        Instant lastSeenAt
) {
    public static CurrentUserResponse from(AppUser user) {
        return new CurrentUserResponse(
                user.getId(),
                user.getUsername(),
                user.getEmail(),
                user.getDisplayName(),
                user.getAuthProvider(),
                user.getCreatedAt(),
                user.getLastSeenAt()
        );
    }
}
