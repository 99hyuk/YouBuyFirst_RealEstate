package com.youbuyfirst.backend.auth;

import org.junit.jupiter.api.Test;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.client.oidc.userinfo.OidcUserRequest;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserService;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.core.OAuth2AccessToken;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.oidc.user.DefaultOidcUser;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;

import java.time.Instant;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class AppOidcUserServiceTest {

    @Test
    void mapsGoogleOidcUserToAppPrincipal() {
        OAuthAccountService oauthAccountService = mock(OAuthAccountService.class);
        Instant now = Instant.parse("2026-06-25T09:00:00Z");
        AppUser appUser = AppUser.oauth(
                "googleuser",
                "google-user@example.com",
                "Google User",
                "{noop}oauth",
                "google",
                now
        );
        when(oauthAccountService.findOrCreateUser(new OAuthProviderProfile(
                "google",
                "google-subject-1",
                "google-user@example.com",
                "Google User"
        ))).thenReturn(appUser);

        OidcIdToken idToken = new OidcIdToken(
                "id-token",
                now,
                now.plusSeconds(300),
                Map.of(
                        "sub", "google-subject-1",
                        "email", "google-user@example.com",
                        "name", "Google User"
                )
        );
        OidcUser googleUser = new DefaultOidcUser(
                List.of(new SimpleGrantedAuthority("OIDC_USER")),
                idToken
        );
        OAuth2UserService<OidcUserRequest, OidcUser> delegate = request -> googleUser;
        AppOidcUserService service = new AppOidcUserService(oauthAccountService, delegate);

        OidcUser result = service.loadUser(new OidcUserRequest(
                googleRegistration(),
                new OAuth2AccessToken(OAuth2AccessToken.TokenType.BEARER, "access-token", now, now.plusSeconds(300)),
                idToken
        ));

        assertThat(result).isInstanceOf(AppUserPrincipal.class);
        AppUserPrincipal principal = (AppUserPrincipal) result;
        assertThat(principal.getUserId()).isEqualTo(appUser.getId());
        assertThat(principal.getAppUsername()).isEqualTo("googleuser");
        assertThat(principal.getEmail()).isEqualTo("google-user@example.com");
        assertThat(result.getIdToken()).isEqualTo(idToken);
        verify(oauthAccountService).findOrCreateUser(new OAuthProviderProfile(
                "google",
                "google-subject-1",
                "google-user@example.com",
                "Google User"
        ));
    }

    private static ClientRegistration googleRegistration() {
        return ClientRegistration.withRegistrationId("google")
                .clientId("google-client")
                .clientSecret("google-secret")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("{baseUrl}/login/oauth2/code/{registrationId}")
                .authorizationUri("https://accounts.google.com/o/oauth2/v2/auth")
                .tokenUri("https://oauth2.googleapis.com/token")
                .jwkSetUri("https://www.googleapis.com/oauth2/v3/certs")
                .issuerUri("https://accounts.google.com")
                .userInfoUri("https://openidconnect.googleapis.com/v1/userinfo")
                .userNameAttributeName("sub")
                .scope("openid", "profile", "email")
                .clientName("Google")
                .build();
    }
}
