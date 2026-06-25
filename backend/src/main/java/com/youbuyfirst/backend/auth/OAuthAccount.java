package com.youbuyfirst.backend.auth;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "user_oauth_accounts")
public class OAuthAccount {

    @Id
    @Column(length = 36)
    private String id;

    @ManyToOne(fetch = FetchType.EAGER, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private AppUser user;

    @Column(nullable = false, length = 40)
    private String provider;

    @Column(name = "provider_user_id", nullable = false, length = 128)
    private String providerUserId;

    @Column(length = 255)
    private String email;

    @Column(name = "display_name", length = 100)
    private String displayName;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "last_login_at", nullable = false)
    private Instant lastLoginAt;

    protected OAuthAccount() {
    }

    private OAuthAccount(
            String id,
            AppUser user,
            String provider,
            String providerUserId,
            String email,
            String displayName,
            Instant createdAt,
            Instant lastLoginAt
    ) {
        this.id = id;
        this.user = user;
        this.provider = provider;
        this.providerUserId = providerUserId;
        this.email = email;
        this.displayName = displayName;
        this.createdAt = createdAt;
        this.lastLoginAt = lastLoginAt;
    }

    public static OAuthAccount link(AppUser user, OAuthProviderProfile profile, Instant now) {
        return new OAuthAccount(
                UUID.randomUUID().toString(),
                user,
                profile.provider(),
                profile.providerUserId(),
                profile.email(),
                profile.displayName(),
                now,
                now
        );
    }

    public void markLogin(OAuthProviderProfile profile, Instant now) {
        this.email = profile.email();
        this.displayName = profile.displayName();
        this.lastLoginAt = now;
    }

    public AppUser getUser() {
        return user;
    }

    public String getProvider() {
        return provider;
    }

    public String getProviderUserId() {
        return providerUserId;
    }

    public Instant getLastLoginAt() {
        return lastLoginAt;
    }
}
