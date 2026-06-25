package com.youbuyfirst.backend.auth;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Condition;
import org.springframework.context.annotation.ConditionContext;
import org.springframework.context.annotation.Conditional;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;
import org.springframework.core.type.AnnotatedTypeMetadata;
import org.springframework.security.config.oauth2.client.CommonOAuth2Provider;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.client.registration.InMemoryClientRegistrationRepository;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.util.StringUtils;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Configuration
public class OAuthClientRegistrationConfig {

    private static final String DEFAULT_REDIRECT_URI = "{baseUrl}/login/oauth2/code/{registrationId}";

    @Bean
    @Conditional(OAuthClientsConfiguredCondition.class)
    ClientRegistrationRepository clientRegistrationRepository(Environment environment) {
        List<ClientRegistration> registrations = new ArrayList<>();
        google(environment).ifPresent(registrations::add);
        naver(environment).ifPresent(registrations::add);
        kakao(environment).ifPresent(registrations::add);
        return new InMemoryClientRegistrationRepository(registrations);
    }

    private static Optional<ClientRegistration> google(Environment environment) {
        Credentials credentials = credentials(environment, "google");
        if (!credentials.hasClientIdAndSecret()) {
            return Optional.empty();
        }

        return Optional.of(CommonOAuth2Provider.GOOGLE.getBuilder("google")
                .clientId(credentials.clientId())
                .clientSecret(credentials.clientSecret())
                .redirectUri(redirectUri(environment))
                .scope("openid", "profile", "email")
                .build());
    }

    private static Optional<ClientRegistration> naver(Environment environment) {
        Credentials credentials = credentials(environment, "naver");
        if (!credentials.hasClientIdAndSecret()) {
            return Optional.empty();
        }

        return Optional.of(ClientRegistration.withRegistrationId("naver")
                .clientId(credentials.clientId())
                .clientSecret(credentials.clientSecret())
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_POST)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri(redirectUri(environment))
                .authorizationUri("https://nid.naver.com/oauth2.0/authorize")
                .tokenUri("https://nid.naver.com/oauth2.0/token")
                .userInfoUri("https://openapi.naver.com/v1/nid/me")
                .userNameAttributeName("response")
                .clientName("Naver")
                .build());
    }

    private static Optional<ClientRegistration> kakao(Environment environment) {
        Credentials credentials = credentials(environment, "kakao");
        if (!StringUtils.hasText(credentials.clientId())) {
            return Optional.empty();
        }

        ClientAuthenticationMethod authenticationMethod = StringUtils.hasText(credentials.clientSecret())
                ? ClientAuthenticationMethod.CLIENT_SECRET_POST
                : ClientAuthenticationMethod.NONE;

        ClientRegistration.Builder builder = ClientRegistration.withRegistrationId("kakao")
                .clientId(credentials.clientId())
                .clientAuthenticationMethod(authenticationMethod)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri(redirectUri(environment))
                .authorizationUri("https://kauth.kakao.com/oauth/authorize")
                .tokenUri("https://kauth.kakao.com/oauth/token")
                .userInfoUri("https://kapi.kakao.com/v2/user/me")
                .userNameAttributeName("id")
                .clientName("Kakao");

        if (StringUtils.hasText(credentials.clientSecret())) {
            builder.clientSecret(credentials.clientSecret());
        }

        return Optional.of(builder.build());
    }

    private static String redirectUri(Environment environment) {
        String redirectBaseUrl = globalProperty(environment, "redirect-base-url");
        if (!StringUtils.hasText(redirectBaseUrl)) {
            return DEFAULT_REDIRECT_URI;
        }
        return redirectBaseUrl.replaceAll("/+$", "") + "/login/oauth2/code/{registrationId}";
    }

    private static Credentials credentials(Environment environment, String provider) {
        return new Credentials(
                property(environment, provider, "client-id"),
                property(environment, provider, "client-secret")
        );
    }

    private static String property(Environment environment, String provider, String name) {
        String configured = environment.getProperty("app.auth.oauth." + provider + "." + name);
        if (StringUtils.hasText(configured)) {
            return configured.trim();
        }

        String envName = "OAUTH_" + provider.toUpperCase(java.util.Locale.ROOT) + "_"
                + name.toUpperCase(java.util.Locale.ROOT).replace("-", "_");
        String fromEnv = environment.getProperty(envName);
        return StringUtils.hasText(fromEnv) ? fromEnv.trim() : "";
    }

    private static String globalProperty(Environment environment, String name) {
        String configured = environment.getProperty("app.auth.oauth." + name);
        if (StringUtils.hasText(configured)) {
            return configured.trim();
        }

        String envName = "APP_AUTH_OAUTH_" + name.toUpperCase(java.util.Locale.ROOT).replace("-", "_");
        String fromEnv = environment.getProperty(envName);
        return StringUtils.hasText(fromEnv) ? fromEnv.trim() : "";
    }

    private record Credentials(String clientId, String clientSecret) {
        boolean hasClientIdAndSecret() {
            return StringUtils.hasText(clientId) && StringUtils.hasText(clientSecret);
        }
    }

    static class OAuthClientsConfiguredCondition implements Condition {
        @Override
        public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
            Environment environment = context.getEnvironment();
            return credentials(environment, "google").hasClientIdAndSecret()
                    || credentials(environment, "naver").hasClientIdAndSecret()
                    || StringUtils.hasText(credentials(environment, "kakao").clientId());
        }
    }
}
