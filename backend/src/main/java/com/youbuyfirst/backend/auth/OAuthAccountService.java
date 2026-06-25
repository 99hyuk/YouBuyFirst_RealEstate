package com.youbuyfirst.backend.auth;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Locale;
import java.util.UUID;

@Service
public class OAuthAccountService {

    private static final int USERNAME_MAX_LENGTH = 20;
    private static final int DISPLAY_NAME_MAX_LENGTH = 20;

    private final AppUserRepository appUserRepository;
    private final OAuthAccountRepository oauthAccountRepository;
    private final PasswordEncoder passwordEncoder;

    public OAuthAccountService(
            AppUserRepository appUserRepository,
            OAuthAccountRepository oauthAccountRepository,
            PasswordEncoder passwordEncoder
    ) {
        this.appUserRepository = appUserRepository;
        this.oauthAccountRepository = oauthAccountRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public AppUser findOrCreateUser(OAuthProviderProfile profile) {
        Instant now = Instant.now();
        return oauthAccountRepository.findByProviderAndProviderUserId(profile.provider(), profile.providerUserId())
                .map(account -> {
                    account.markLogin(profile, now);
                    account.getUser().markSeen(now);
                    return account.getUser();
                })
                .orElseGet(() -> linkNewProviderIdentity(profile, now));
    }

    private AppUser linkNewProviderIdentity(OAuthProviderProfile profile, Instant now) {
        AppUser user = findExistingUserByEmail(profile)
                .orElseGet(() -> createOAuthUser(profile, now));
        user.markSeen(now);
        oauthAccountRepository.save(OAuthAccount.link(user, profile, now));
        return user;
    }

    private java.util.Optional<AppUser> findExistingUserByEmail(OAuthProviderProfile profile) {
        if (profile.email().isBlank()) {
            return java.util.Optional.empty();
        }
        return appUserRepository.findByEmail(AuthSupport.normalizeEmail(profile.email()));
    }

    private AppUser createOAuthUser(OAuthProviderProfile profile, Instant now) {
        String username = uniqueUsername(profile);
        String email = uniqueEmail(profile);
        String displayName = uniqueDisplayName(profile);
        String passwordHash = passwordEncoder.encode("oauth-" + UUID.randomUUID());
        return appUserRepository.save(AppUser.oauth(
                username,
                email,
                displayName,
                passwordHash,
                profile.provider(),
                now
        ));
    }

    private String uniqueUsername(OAuthProviderProfile profile) {
        String localPart = profile.email().contains("@") ? profile.email().split("@", 2)[0] : "";
        String base = alphanumeric(localPart);
        if (base.length() < 4) {
            base = alphanumeric(profile.provider() + hash(profile.providerUserId()));
        }
        if (base.length() < 4) {
            base = "user" + shortHash(profile.provider() + profile.providerUserId());
        }
        base = trim(base.toLowerCase(Locale.ROOT), USERNAME_MAX_LENGTH);

        String candidate = base;
        int attempt = 0;
        while (appUserRepository.existsByUsername(candidate)) {
            String suffix = shortHash(profile.provider() + profile.providerUserId() + attempt);
            candidate = trim(base, USERNAME_MAX_LENGTH - suffix.length()) + suffix;
            attempt++;
        }
        return candidate;
    }

    private String uniqueEmail(OAuthProviderProfile profile) {
        if (!profile.email().isBlank() && appUserRepository.findByEmail(profile.email()).isEmpty()) {
            return profile.email();
        }

        String local = trim(profile.provider() + "-" + shortHash(profile.providerUserId()), 64);
        String candidate = local + "@oauth.local";
        int attempt = 0;
        while (appUserRepository.existsByEmail(candidate)) {
            String suffix = shortHash(profile.providerUserId() + attempt);
            candidate = trim(local, 64 - suffix.length()) + suffix + "@oauth.local";
            attempt++;
        }
        return candidate;
    }

    private String uniqueDisplayName(OAuthProviderProfile profile) {
        String base = profile.displayName().isBlank()
                ? profile.provider() + " user"
                : profile.displayName();
        base = trim(base, DISPLAY_NAME_MAX_LENGTH);

        String candidate = base;
        int attempt = 0;
        while (appUserRepository.existsByDisplayName(candidate)) {
            String suffix = "-" + shortHash(profile.provider() + profile.providerUserId() + attempt).substring(0, 4);
            candidate = trim(base, DISPLAY_NAME_MAX_LENGTH - suffix.length()) + suffix;
            attempt++;
        }
        return candidate;
    }

    private static String alphanumeric(String value) {
        return value == null ? "" : value.replaceAll("[^A-Za-z0-9]", "");
    }

    private static String trim(String value, int maxLength) {
        String trimmed = value == null ? "" : value.trim();
        if (trimmed.length() <= maxLength) {
            return trimmed;
        }
        return trimmed.substring(0, Math.max(0, maxLength));
    }

    private static String shortHash(String value) {
        return hash(value).substring(0, 8);
    }

    private static String hash(String value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(value.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException("SHA-256 is required", ex);
        }
    }
}
