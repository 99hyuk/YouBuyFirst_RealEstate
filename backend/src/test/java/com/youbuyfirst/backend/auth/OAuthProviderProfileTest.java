package com.youbuyfirst.backend.auth;

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class OAuthProviderProfileTest {

    @Test
    void extractsGoogleProfile() {
        OAuthProviderProfile profile = OAuthProviderProfile.from(
                "google",
                Map.of(
                        "sub", "google-subject-1",
                        "email", "buyer@example.com",
                        "name", "Google Buyer"
                )
        );

        assertThat(profile.provider()).isEqualTo("google");
        assertThat(profile.providerUserId()).isEqualTo("google-subject-1");
        assertThat(profile.email()).isEqualTo("buyer@example.com");
        assertThat(profile.displayName()).isEqualTo("Google Buyer");
    }

    @Test
    void extractsNaverProfileFromResponseWrapper() {
        OAuthProviderProfile profile = OAuthProviderProfile.from(
                "naver",
                Map.of("response", Map.of(
                        "id", "naver-subject-1",
                        "email", "buyer@naver.com",
                        "nickname", "Naver Buyer"
                ))
        );

        assertThat(profile.provider()).isEqualTo("naver");
        assertThat(profile.providerUserId()).isEqualTo("naver-subject-1");
        assertThat(profile.email()).isEqualTo("buyer@naver.com");
        assertThat(profile.displayName()).isEqualTo("Naver Buyer");
    }

    @Test
    void extractsKakaoProfileFromAccountWrapper() {
        OAuthProviderProfile profile = OAuthProviderProfile.from(
                "kakao",
                Map.of(
                        "id", 123456789L,
                        "kakao_account", Map.of(
                                "email", "buyer@kakao.com",
                                "profile", Map.of("nickname", "Kakao Buyer")
                        )
                )
        );

        assertThat(profile.provider()).isEqualTo("kakao");
        assertThat(profile.providerUserId()).isEqualTo("123456789");
        assertThat(profile.email()).isEqualTo("buyer@kakao.com");
        assertThat(profile.displayName()).isEqualTo("Kakao Buyer");
    }
}
