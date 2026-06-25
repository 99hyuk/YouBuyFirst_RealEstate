package com.youbuyfirst.backend.auth;

import org.junit.jupiter.api.Test;
import org.springframework.mock.env.MockEnvironment;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;

import static org.assertj.core.api.Assertions.assertThat;

class OAuthClientRegistrationConfigTest {

    @Test
    void usesConfiguredRedirectBaseUrlForProviderCallbacks() {
        MockEnvironment environment = new MockEnvironment()
                .withProperty("OAUTH_GOOGLE_CLIENT_ID", "google-client")
                .withProperty("OAUTH_GOOGLE_CLIENT_SECRET", "google-secret")
                .withProperty(
                        "APP_AUTH_OAUTH_REDIRECT_BASE_URL",
                        "https://planner-happy-chair.ngrok-free.dev/"
                );

        ClientRegistrationRepository registrations = new OAuthClientRegistrationConfig()
                .clientRegistrationRepository(environment);
        ClientRegistration google = registrations.findByRegistrationId("google");

        assertThat(google).isNotNull();
        assertThat(google.getRedirectUri()).isEqualTo(
                "https://planner-happy-chair.ngrok-free.dev/login/oauth2/code/{registrationId}"
        );
    }
}
