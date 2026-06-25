package com.youbuyfirst.backend.auth;

import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.ProviderManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.oauth2.client.oidc.userinfo.OidcUserRequest;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserService;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.AuthenticationFailureHandler;
import org.springframework.security.web.authentication.AuthenticationSuccessHandler;

@Configuration
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(
            HttpSecurity http,
            ObjectProvider<ClientRegistrationRepository> clientRegistrationRepository,
            OAuth2UserService<OAuth2UserRequest, OAuth2User> oauth2UserService,
            OAuth2UserService<OidcUserRequest, OidcUser> oidcUserService,
            AuthenticationSuccessHandler oauthAuthenticationSuccessHandler,
            AuthenticationFailureHandler oauthAuthenticationFailureHandler
    ) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .formLogin(AbstractHttpConfigurer::disable)
                .httpBasic(AbstractHttpConfigurer::disable)
                .logout(AbstractHttpConfigurer::disable)
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED))
                .exceptionHandling(exceptionHandling -> exceptionHandling.authenticationEntryPoint(
                        (request, response, authException) -> response.sendError(HttpServletResponse.SC_UNAUTHORIZED)
                ))
                .authorizeHttpRequests(authorize -> authorize
                        .requestMatchers(HttpMethod.GET, "/api/auth/me").authenticated()
                        .requestMatchers(HttpMethod.POST, "/api/auth/logout").authenticated()
                        .requestMatchers("/api/realestate/watch-targets", "/api/realestate/watch-targets/**").authenticated()
                        .anyRequest().permitAll()
                );

        if (clientRegistrationRepository.getIfAvailable() != null) {
            http.oauth2Login(oauth -> oauth
                    .userInfoEndpoint(userInfo -> userInfo
                            .userService(oauth2UserService)
                            .oidcUserService(oidcUserService)
                    )
                    .successHandler(oauthAuthenticationSuccessHandler)
                    .failureHandler(oauthAuthenticationFailureHandler)
            );
        }

        return http.build();
    }

    @Bean
    public AuthenticationManager authenticationManager(
            UserDetailsService userDetailsService,
            PasswordEncoder passwordEncoder
    ) {
        DaoAuthenticationProvider provider = new DaoAuthenticationProvider();
        provider.setUserDetailsService(userDetailsService);
        provider.setPasswordEncoder(passwordEncoder);
        return new ProviderManager(provider);
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
