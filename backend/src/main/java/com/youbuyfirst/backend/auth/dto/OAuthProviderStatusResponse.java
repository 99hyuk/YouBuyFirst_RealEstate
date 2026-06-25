package com.youbuyfirst.backend.auth.dto;

public record OAuthProviderStatusResponse(
        String provider,
        String displayName,
        String authorizationUrl,
        boolean configured
) {
}
