package com.youbuyfirst.backend.chat;

import org.springframework.boot.web.servlet.ServletListenerRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ChatPresenceConfiguration {

    @Bean
    public ServletListenerRegistrationBean<ChatPresenceCounter> chatPresenceSessionListener(
            ChatPresenceCounter counter
    ) {
        return new ServletListenerRegistrationBean<>(counter);
    }
}
