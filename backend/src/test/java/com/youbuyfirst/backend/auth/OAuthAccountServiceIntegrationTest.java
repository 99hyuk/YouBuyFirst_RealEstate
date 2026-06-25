package com.youbuyfirst.backend.auth;

import com.youbuyfirst.backend.auth.dto.RegisterRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
class OAuthAccountServiceIntegrationTest {

    @Autowired
    private AuthService authService;

    @Autowired
    private OAuthAccountService oauthAccountService;

    @Autowired
    private OAuthAccountRepository oauthAccountRepository;

    @Test
    void createsUserAndProviderIdentityFromSocialProfile() {
        AppUser user = oauthAccountService.findOrCreateUser(new OAuthProviderProfile(
                "kakao",
                "kakao-social-1",
                "social-kakao@example.com",
                "Kakao Social"
        ));

        assertThat(user.getAuthProvider()).isEqualTo("kakao");
        assertThat(user.getEmail()).isEqualTo("social-kakao@example.com");
        assertThat(user.getDisplayName()).isEqualTo("Kakao Social");
        assertThat(oauthAccountRepository.findByProviderAndProviderUserId("kakao", "kakao-social-1"))
                .hasValueSatisfying(account -> assertThat(account.getUser().getId()).isEqualTo(user.getId()));
    }

    @Test
    void linksNewProviderIdentityToExistingEmailAccount() {
        AppUser localUser = authService.register(new RegisterRequest(
                "oauthlink01",
                "oauth-link@example.com",
                "watch-1234!",
                "OAuth Link"
        ));

        AppUser linkedUser = oauthAccountService.findOrCreateUser(new OAuthProviderProfile(
                "google",
                "google-link-1",
                "OAUTH-LINK@example.com",
                "Google Link"
        ));

        assertThat(linkedUser.getId()).isEqualTo(localUser.getId());
        assertThat(linkedUser.getAuthProvider()).isEqualTo("local");
        assertThat(oauthAccountRepository.findByProviderAndProviderUserId("google", "google-link-1"))
                .hasValueSatisfying(account -> assertThat(account.getUser().getId()).isEqualTo(localUser.getId()));
    }
}
