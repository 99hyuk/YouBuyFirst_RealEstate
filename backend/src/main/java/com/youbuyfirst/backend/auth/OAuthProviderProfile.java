package com.youbuyfirst.backend.auth;

import java.util.Locale;
import java.util.Map;

public record OAuthProviderProfile(
        String provider,
        String providerUserId,
        String email,
        String displayName
) {
    public OAuthProviderProfile {
        provider = text(provider).toLowerCase(Locale.ROOT);
        providerUserId = text(providerUserId);
        email = AuthSupport.normalizeEmail(email);
        displayName = AuthSupport.normalizeDisplayName(displayName);
        if (provider.isBlank()) {
            throw new IllegalArgumentException("OAuth provider is required");
        }
        if (providerUserId.isBlank()) {
            throw new IllegalArgumentException("OAuth provider user id is required");
        }
    }

    public static OAuthProviderProfile from(String registrationId, Map<String, Object> attributes) {
        String provider = text(registrationId).toLowerCase(Locale.ROOT);
        return switch (provider) {
            case "google" -> fromGoogle(attributes);
            case "naver" -> fromNaver(attributes);
            case "kakao" -> fromKakao(attributes);
            default -> throw new IllegalArgumentException("Unsupported OAuth provider: " + registrationId);
        };
    }

    private static OAuthProviderProfile fromGoogle(Map<String, Object> attributes) {
        return new OAuthProviderProfile(
                "google",
                text(attributes.get("sub")),
                text(attributes.get("email")),
                text(attributes.get("name"))
        );
    }

    private static OAuthProviderProfile fromNaver(Map<String, Object> attributes) {
        Map<String, Object> response = nestedMap(attributes.get("response"));
        return new OAuthProviderProfile(
                "naver",
                text(response.get("id")),
                text(response.get("email")),
                firstText(response.get("nickname"), response.get("name"))
        );
    }

    private static OAuthProviderProfile fromKakao(Map<String, Object> attributes) {
        Map<String, Object> account = nestedMap(attributes.get("kakao_account"));
        Map<String, Object> profile = nestedMap(account.get("profile"));
        return new OAuthProviderProfile(
                "kakao",
                text(attributes.get("id")),
                text(account.get("email")),
                firstText(profile.get("nickname"), attributes.get("properties.nickname"))
        );
    }

    private static Map<String, Object> nestedMap(Object value) {
        if (value instanceof Map<?, ?> map) {
            return map.entrySet().stream()
                    .filter(entry -> entry.getKey() instanceof String)
                    .collect(
                            java.util.stream.Collectors.toMap(
                                    entry -> (String) entry.getKey(),
                                    Map.Entry::getValue
                            )
                    );
        }
        return Map.of();
    }

    private static String firstText(Object first, Object second) {
        String value = text(first);
        return value.isBlank() ? text(second) : value;
    }

    private static String text(Object value) {
        return value == null ? "" : String.valueOf(value).trim();
    }
}
