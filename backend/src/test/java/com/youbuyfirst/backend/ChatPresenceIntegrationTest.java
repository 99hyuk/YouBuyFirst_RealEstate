package com.youbuyfirst.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class ChatPresenceIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void returnsActiveChatHeartbeatCountForChatPresence() throws Exception {
        ResponseEntity<String> presence = restTemplate.getForEntity("/api/chat/presence", String.class);

        assertThat(presence.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(presence.getHeaders().getOrEmpty(HttpHeaders.SET_COOKIE))
                .anyMatch(cookie -> cookie.startsWith("JSESSIONID="));

        JsonNode body = objectMapper.readTree(presence.getBody());
        assertThat(body.path("activeSessionCount").asInt()).isGreaterThanOrEqualTo(1);
        assertThat(body.path("source").asText()).isEqualTo("chat_presence_heartbeat");
    }
}
