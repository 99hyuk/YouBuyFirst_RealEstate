package com.youbuyfirst.backend.auth;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface OAuthAccountRepository extends JpaRepository<OAuthAccount, String> {
    Optional<OAuthAccount> findByProviderAndProviderUserId(String provider, String providerUserId);
}
