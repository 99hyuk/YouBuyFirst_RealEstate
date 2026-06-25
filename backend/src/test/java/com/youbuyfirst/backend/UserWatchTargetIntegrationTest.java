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

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class UserWatchTargetIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @LocalServerPort
    private int port;

    @Test
    void requiresLoggedInSessionForUserWatchTargets() throws Exception {
        ResponseEntity<String> list = restTemplate.getForEntity("/api/realestate/watch-targets", String.class);
        HttpRequest save = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/api/realestate/watch-targets"))
                .header(HttpHeaders.CONTENT_TYPE, "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(
                        """
                        {
                          "targetType": "region",
                          "targetId": "region-seoul-mapo",
                          "displayName": "서울 마포구",
                          "landingPath": "/realestate/map/region-seoul?selectedTargetId=region-seoul-mapo"
                        }
                        """,
                        StandardCharsets.UTF_8
                ))
                .build();
        HttpResponse<String> saveResponse = HttpClient.newHttpClient().send(
                save,
                HttpResponse.BodyHandlers.ofString()
        );

        assertThat(list.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
        assertThat(saveResponse.statusCode()).isEqualTo(HttpStatus.UNAUTHORIZED.value());
    }

    @Test
    void savesListsAndRemovesWatchTargetsPerSessionUser() throws Exception {
        HttpHeaders firstUserHeaders = sessionHeaders(register(
                "watchuser01",
                "watch-user-01@example.com",
                "Watch User One"
        ));
        HttpHeaders secondUserHeaders = sessionHeaders(register(
                "watchuser02",
                "watch-user-02@example.com",
                "Watch User Two"
        ));

        ResponseEntity<String> savedRegion = restTemplate.exchange(
                "/api/realestate/watch-targets",
                HttpMethod.POST,
                new HttpEntity<>(Map.of(
                        "targetType", "region",
                        "targetId", "region-seoul-mapo",
                        "displayName", "서울 마포구",
                        "landingPath", "/realestate/map/region-seoul?selectedTargetId=region-seoul-mapo&selectedRegionCode=11140&period=week"
                ), firstUserHeaders),
                String.class
        );
        ResponseEntity<String> savedComplex = restTemplate.exchange(
                "/api/realestate/watch-targets",
                HttpMethod.POST,
                new HttpEntity<>(Map.of(
                        "targetType", "complex",
                        "targetId", "complex-mock-raemian-daechi",
                        "displayName", "래미안대치팰리스",
                        "landingPath", "/realestate/transactions?region=11680&selected=complex-mock-raemian-daechi"
                ), firstUserHeaders),
                String.class
        );

        assertThat(savedRegion.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(savedComplex.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        JsonNode savedRegionBody = objectMapper.readTree(savedRegion.getBody());
        assertThat(savedRegionBody.path("targetType").asText()).isEqualTo("region");
        assertThat(savedRegionBody.path("targetId").asText()).isEqualTo("region-seoul-mapo");
        assertThat(savedRegionBody.path("landingPath").asText()).contains("/realestate/map/region-seoul");

        ResponseEntity<String> firstUserList = restTemplate.exchange(
                "/api/realestate/watch-targets",
                HttpMethod.GET,
                new HttpEntity<>(firstUserHeaders),
                String.class
        );
        ResponseEntity<String> secondUserList = restTemplate.exchange(
                "/api/realestate/watch-targets",
                HttpMethod.GET,
                new HttpEntity<>(secondUserHeaders),
                String.class
        );

        JsonNode firstItems = objectMapper.readTree(firstUserList.getBody()).path("items");
        JsonNode secondItems = objectMapper.readTree(secondUserList.getBody()).path("items");

        assertThat(firstUserList.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(firstItems).hasSize(2);
        assertThat(firstItems.findValuesAsText("targetId")).containsExactly(
                "complex-mock-raemian-daechi",
                "region-seoul-mapo"
        );
        assertThat(firstItems.findValuesAsText("displayName")).contains("서울 마포구", "래미안대치팰리스");
        assertThat(secondUserList.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(secondItems).isEmpty();

        ResponseEntity<String> duplicateRegion = restTemplate.exchange(
                "/api/realestate/watch-targets",
                HttpMethod.POST,
                new HttpEntity<>(Map.of(
                        "targetType", "region",
                        "targetId", "region-seoul-mapo",
                        "displayName", "마포구 지역 리포트",
                        "landingPath", "/realestate/map/region-seoul?selectedTargetId=region-seoul-mapo&selectedRegionCode=11140&period=month"
                ), firstUserHeaders),
                String.class
        );
        ResponseEntity<String> afterDuplicate = restTemplate.exchange(
                "/api/realestate/watch-targets",
                HttpMethod.GET,
                new HttpEntity<>(firstUserHeaders),
                String.class
        );

        assertThat(duplicateRegion.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode afterDuplicateItems = objectMapper.readTree(afterDuplicate.getBody()).path("items");
        assertThat(afterDuplicateItems).hasSize(2);
        JsonNode updatedRegion = findByTargetId(afterDuplicateItems, "region-seoul-mapo");
        assertThat(updatedRegion.path("displayName").asText()).isEqualTo("마포구 지역 리포트");
        assertThat(updatedRegion.path("landingPath").asText()).contains("period=month");

        ResponseEntity<String> removed = restTemplate.exchange(
                "/api/realestate/watch-targets?targetType=region&targetId=region-seoul-mapo",
                HttpMethod.DELETE,
                new HttpEntity<>(firstUserHeaders),
                String.class
        );
        ResponseEntity<String> afterRemove = restTemplate.exchange(
                "/api/realestate/watch-targets",
                HttpMethod.GET,
                new HttpEntity<>(firstUserHeaders),
                String.class
        );

        assertThat(removed.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
        JsonNode remainingItems = objectMapper.readTree(afterRemove.getBody()).path("items");
        assertThat(remainingItems).hasSize(1);
        assertThat(remainingItems.get(0).path("targetId").asText()).isEqualTo("complex-mock-raemian-daechi");
    }

    private ResponseEntity<String> register(String username, String email, String displayName) {
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

    private static HttpHeaders sessionHeaders(ResponseEntity<String> response) {
        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.COOKIE, sessionCookieHeader(response));
        return headers;
    }

    private static String sessionCookieHeader(ResponseEntity<String> response) {
        return sessionCookieHeaders(response)
                .stream()
                .map(cookie -> cookie.split(";", 2)[0])
                .findFirst()
                .orElseThrow(() -> new AssertionError("No JSESSIONID cookie returned"));
    }

    private static List<String> sessionCookieHeaders(ResponseEntity<String> response) {
        return response.getHeaders()
                .getOrEmpty(HttpHeaders.SET_COOKIE)
                .stream()
                .filter(cookie -> cookie.startsWith("JSESSIONID="))
                .toList();
    }

    private static JsonNode findByTargetId(JsonNode items, String targetId) {
        for (JsonNode item : items) {
            if (targetId.equals(item.path("targetId").asText())) {
                return item;
            }
        }
        throw new AssertionError("No watch target found for " + targetId);
    }
}
