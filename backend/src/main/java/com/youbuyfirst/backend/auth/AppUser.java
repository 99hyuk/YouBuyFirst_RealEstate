package com.youbuyfirst.backend.auth;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "app_users")
public class AppUser {

    @Id
    @Column(length = 36)
    private String id;

    @Column(nullable = false, length = 20)
    private String username;

    @Column(nullable = false, length = 255)
    private String email;

    @Column(name = "display_name", nullable = false, length = 20)
    private String displayName;

    @Column(name = "password_hash", nullable = false, length = 255)
    private String passwordHash;

    @Column(name = "auth_provider", nullable = false, length = 40)
    private String authProvider;

    @Column(nullable = false, length = 30)
    private String role;

    @Column(nullable = false, length = 30)
    private String status;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "last_seen_at")
    private Instant lastSeenAt;

    protected AppUser() {
    }

    private AppUser(
            String id,
            String username,
            String email,
            String displayName,
            String passwordHash,
            String authProvider,
            String role,
            String status,
            Instant createdAt,
            Instant lastSeenAt
    ) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.displayName = displayName;
        this.passwordHash = passwordHash;
        this.authProvider = authProvider;
        this.role = role;
        this.status = status;
        this.createdAt = createdAt;
        this.lastSeenAt = lastSeenAt;
    }

    public static AppUser local(String username, String email, String displayName, String passwordHash, Instant now) {
        return new AppUser(
                UUID.randomUUID().toString(),
                username,
                email,
                displayName,
                passwordHash,
                "local",
                "USER",
                "active",
                now,
                now
        );
    }

    public static AppUser oauth(
            String username,
            String email,
            String displayName,
            String passwordHash,
            String authProvider,
            Instant now
    ) {
        return new AppUser(
                UUID.randomUUID().toString(),
                username,
                email,
                displayName,
                passwordHash,
                authProvider,
                "USER",
                "active",
                now,
                now
        );
    }

    public void markSeen(Instant now) {
        this.lastSeenAt = now;
    }

    public String getId() {
        return id;
    }

    public String getUsername() {
        return username;
    }

    public String getEmail() {
        return email;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getPasswordHash() {
        return passwordHash;
    }

    public String getAuthProvider() {
        return authProvider;
    }

    public String getRole() {
        return role;
    }

    public String getStatus() {
        return status;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getLastSeenAt() {
        return lastSeenAt;
    }
}
