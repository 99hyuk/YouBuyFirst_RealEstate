package com.youbuyfirst.backend.auth;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.web.authentication.AuthenticationFailureHandler;
import org.springframework.security.web.authentication.AuthenticationSuccessHandler;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationFailureHandler;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;

@Configuration
public class OAuthLoginHandlers {

    @Bean
    AuthenticationSuccessHandler oauthAuthenticationSuccessHandler(
            @Value("${app.auth.oauth.success-redirect:/dashboard}") String successRedirect
    ) {
        SimpleUrlAuthenticationSuccessHandler handler = new SimpleUrlAuthenticationSuccessHandler(successRedirect);
        handler.setAlwaysUseDefaultTargetUrl(true);
        return handler;
    }

    @Bean
    AuthenticationFailureHandler oauthAuthenticationFailureHandler(
            @Value("${app.auth.oauth.failure-redirect:/auth/login?oauth=failed}") String failureRedirect
    ) {
        return new SimpleUrlAuthenticationFailureHandler(failureRedirect);
    }
}
