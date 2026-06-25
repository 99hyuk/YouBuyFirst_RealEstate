package com.youbuyfirst.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class ChatMessageIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @LocalServerPort
    private int port;

    @Test
    void storesChatMessagesOnTheServerAndReadsThemWithoutThePostingSession() throws Exception {
        HttpHeaders authHeaders = new HttpHeaders();
        authHeaders.add(HttpHeaders.COOKIE, sessionCookieHeader(registerUser(
                "chatuser01",
                "chatuser01@example.com",
                "행복"
        )));

        ResponseEntity<String> posted = restTemplate.exchange(
                "/api/chat/messages",
                HttpMethod.POST,
                new HttpEntity<>(Map.of(
                        "body", "localhost에서 보낸 서버 채팅",
                        "displayName", "행복한집"
                ), authHeaders),
                String.class
        );

        assertThat(posted.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        JsonNode postedBody = objectMapper.readTree(posted.getBody());
        assertThat(postedBody.path("author").asText()).isEqualTo("행복한집");
        assertThat(postedBody.path("body").asText()).isEqualTo("localhost에서 보낸 서버 채팅");
        assertThat(postedBody.path("category").asText()).isEqualTo("chat");
        assertThat(postedBody.path("mine").asBoolean()).isTrue();
        assertThat(postedBody.path("verified").asBoolean()).isTrue();

        ResponseEntity<String> readWithoutCookie = restTemplate.getForEntity("/api/chat/messages", String.class);

        assertThat(readWithoutCookie.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode messages = objectMapper.readTree(readWithoutCookie.getBody());
        assertThat(messages).anySatisfy(message -> {
            assertThat(message.path("author").asText()).isEqualTo("행복한집");
            assertThat(message.path("body").asText()).isEqualTo("localhost에서 보낸 서버 채팅");
            assertThat(message.path("verified").asBoolean()).isTrue();
        });
    }

    @Test
    void storesGuestChatMessagesWithoutLoginAndMarksThemUnverified() throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/chat/messages"))
                .header(HttpHeaders.CONTENT_TYPE, "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(
                        "{\"body\":\"비로그인도 채팅 참여\",\"displayName\":\"손님분석가\"}",
                        StandardCharsets.UTF_8
                ))
                .build();
        HttpResponse<String> posted = HttpClient.newHttpClient().send(
                request,
                HttpResponse.BodyHandlers.ofString()
        );

        assertThat(posted.statusCode()).isEqualTo(HttpStatus.CREATED.value());
        JsonNode postedBody = objectMapper.readTree(posted.body());
        assertThat(postedBody.path("author").asText()).isEqualTo("손님분석가");
        assertThat(postedBody.path("body").asText()).isEqualTo("비로그인도 채팅 참여");
        assertThat(postedBody.path("mine").asBoolean()).isTrue();
        assertThat(postedBody.path("verified").asBoolean()).isFalse();

        ResponseEntity<String> readWithoutCookie = restTemplate.getForEntity("/api/chat/messages?limit=20", String.class);

        assertThat(readWithoutCookie.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode messages = objectMapper.readTree(readWithoutCookie.getBody());
        assertThat(messages).anySatisfy(message -> {
            assertThat(message.path("author").asText()).isEqualTo("손님분석가");
            assertThat(message.path("verified").asBoolean()).isFalse();
        });
    }

    @Test
    void rejectsGuestChatDisplayNameAlreadyUsedByRegisteredUser() throws Exception {
        registerUser(
                "reservedchat01",
                "reservedchat01@example.com",
                "ReservedBuyer"
        );

        ResponseEntity<String> availability = restTemplate.getForEntity(
                "/api/chat/nickname-availability?displayName={displayName}",
                String.class,
                "ReservedBuyer"
        );

        assertThat(availability.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(objectMapper.readTree(availability.getBody()).path("available").asBoolean()).isFalse();

        HttpRequest request = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/chat/messages"))
                .header(HttpHeaders.CONTENT_TYPE, "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(
                        "{\"body\":\"guest collision\",\"displayName\":\"ReservedBuyer\"}",
                        StandardCharsets.UTF_8
                ))
                .build();
        HttpResponse<String> posted = HttpClient.newHttpClient().send(
                request,
                HttpResponse.BodyHandlers.ofString()
        );

        assertThat(posted.statusCode()).isEqualTo(HttpStatus.CONFLICT.value());
    }

    @Test
    void storesChatMessageAttachmentsAndReadsThemWithLandingPath() throws Exception {
        HttpHeaders authHeaders = new HttpHeaders();
        authHeaders.add(HttpHeaders.COOKIE, sessionCookieHeader(registerUser(
                "attachchat01",
                "attachchat01@example.com",
                "첨부테스터"
        )));

        ResponseEntity<String> posted = restTemplate.exchange(
                "/api/chat/messages",
                HttpMethod.POST,
                new HttpEntity<>(Map.of(
                        "body", "대전 유성구 리포트 같이 봐요",
                        "displayName", "첨부테스터",
                        "attachment", Map.of(
                                "type", "region",
                                "targetId", "region-daejeon-yuseong",
                                "title", "대전 유성구",
                                "subtitle", "지역 분석 · 최근 1주",
                                "metricLabel", "최근 1주",
                                "metricValue", "+0.31%",
                                "metricTone", "up",
                                "landingPath", "/realestate/map/region-daejeon?selectedTargetId=region-daejeon-yuseong&selectedRegionCode=25040&period=week"
                        )
                ), authHeaders),
                String.class
        );

        assertThat(posted.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        JsonNode postedBody = objectMapper.readTree(posted.getBody());
        assertThat(postedBody.path("attachment").path("type").asText()).isEqualTo("region");
        assertThat(postedBody.path("attachment").path("targetId").asText()).isEqualTo("region-daejeon-yuseong");
        assertThat(postedBody.path("attachment").path("metricValue").asText()).isEqualTo("+0.31%");
        assertThat(postedBody.path("verified").asBoolean()).isTrue();
        assertThat(postedBody.path("attachment").path("landingPath").asText())
                .isEqualTo("/realestate/map/region-daejeon?selectedTargetId=region-daejeon-yuseong&selectedRegionCode=25040&period=week");

        ResponseEntity<String> readWithoutCookie = restTemplate.getForEntity("/api/chat/messages?limit=20", String.class);

        assertThat(readWithoutCookie.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode messages = objectMapper.readTree(readWithoutCookie.getBody());
        assertThat(messages).anySatisfy(message -> {
            assertThat(message.path("body").asText()).isEqualTo("대전 유성구 리포트 같이 봐요");
            assertThat(message.path("attachment").path("title").asText()).isEqualTo("대전 유성구");
            assertThat(message.path("attachment").path("landingPath").asText()).contains("/realestate/map/region-daejeon");
        });
    }

    @Test
    void streamsCreatedChatMessagesToOpenClientsWithoutRefresh() throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest streamRequest = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/chat/messages/stream"))
                .GET()
                .build();

        HttpResponse<java.io.InputStream> stream = client.send(
                streamRequest,
                HttpResponse.BodyHandlers.ofInputStream()
        );
        assertThat(stream.statusCode()).isEqualTo(HttpStatus.OK.value());

        ExecutorService executor = Executors.newSingleThreadExecutor();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream.body(), StandardCharsets.UTF_8))) {
            String streamedBody = "새로고침 없이 받는 서버 채팅";
            CompletableFuture<Boolean> sawStreamedMessage = CompletableFuture.supplyAsync(
                    () -> containsSseLine(reader, streamedBody),
                    executor
            );
            HttpHeaders authHeaders = new HttpHeaders();
            authHeaders.add(HttpHeaders.COOKIE, sessionCookieHeader(registerUser(
                    "streamchat01",
                    "streamchat01@example.com",
                    "스트림"
            )));

            ResponseEntity<String> posted = restTemplate.exchange(
                    "/api/chat/messages",
                    HttpMethod.POST,
                    new HttpEntity<>(Map.of(
                            "body", streamedBody,
                            "displayName", "스트림"
                    ), authHeaders),
                    String.class
            );

            assertThat(posted.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(sawStreamedMessage.get(10, TimeUnit.SECONDS)).isTrue();
        } finally {
            executor.shutdownNow();
        }
    }

    private ResponseEntity<String> registerUser(String username, String email, String displayName) {
        return restTemplate.postForEntity(
                "/api/auth/register",
                Map.of(
                        "username", username,
                        "email", email,
                        "password", "watch-1234!",
                        "displayName", displayName
                ),
                String.class
        );
    }

    private static String sessionCookieHeader(ResponseEntity<String> response) {
        return response.getHeaders().getOrEmpty(HttpHeaders.SET_COOKIE)
                .stream()
                .filter(cookie -> cookie.startsWith("JSESSIONID="))
                .findFirst()
                .map(cookie -> cookie.split(";", 2)[0])
                .orElseThrow();
    }

    private static boolean containsSseLine(BufferedReader reader, String expected) {
        try {
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.contains(expected)) {
                    return true;
                }
            }
            return false;
        } catch (IOException ex) {
            throw new CompletionException(ex);
        }
    }
}
