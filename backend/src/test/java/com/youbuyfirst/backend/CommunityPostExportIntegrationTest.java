package com.youbuyfirst.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class CommunityPostExportIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void exportsRecentlyIngestedCommunityPostsForReactionSnapshotBatch() throws Exception {
        Map<String, Object> request = Map.of(
                "source", "TEST_REAL_ESTATE_EXPORT",
                "runId", "test-real-estate-export-2026061401",
                "batchStartedAt", "2026-06-14T01:00:00Z",
                "batchFinishedAt", "2026-06-14T01:00:03Z",
                "posts", List.of(
                        Map.of(
                                "externalId", "export-1",
                                "url", "https://example.com/export-1",
                                "title", "파주시 GTX 기대와 전세 우려가 같이 언급됨",
                                "contentSnippet", "운정 신축과 교통 이슈가 함께 언급됨",
                                "boardId", "realestate",
                                "viewCount", 120,
                                "recommendCount", 4,
                                "commentCount", 9,
                                "authorDisplayName", "sample-author",
                                "publishedAt", "2026-06-14T00:31:00Z"
                        ),
                        Map.of(
                                "externalId", "export-2",
                                "url", "https://example.com/export-2",
                                "title", "대전 유성 공급 부담 글",
                                "contentSnippet", "청약과 공급 이야기가 많음",
                                "boardId", "realestate",
                                "viewCount", 80,
                                "recommendCount", 2,
                                "commentCount", 3,
                                "authorDisplayName", "sample-author-2",
                                "publishedAt", "2026-06-13T23:55:00Z"
                        )
                )
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/ingestions/community-posts",
                request,
                String.class
        );
        ResponseEntity<String> exported = restTemplate.getForEntity(
                "/internal/ingestions/community-posts/export"
                        + "?source=TEST_REAL_ESTATE_EXPORT"
                        + "&publishedFrom=2026-06-14T00:00:00Z"
                        + "&publishedTo=2026-06-14T01:00:00Z"
                        + "&limit=10",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(exported.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode body = objectMapper.readTree(exported.getBody());
        assertThat(body.path("source").asText()).isEqualTo("TEST_REAL_ESTATE_EXPORT");
        assertThat(body.path("publishedFrom").asText()).isEqualTo("2026-06-14T00:00:00Z");
        assertThat(body.path("publishedTo").asText()).isEqualTo("2026-06-14T01:00:00Z");
        assertThat(body.path("items")).hasSize(1);

        JsonNode item = body.path("items").get(0);
        assertThat(item.path("source").asText()).isEqualTo("TEST_REAL_ESTATE_EXPORT");
        assertThat(item.path("externalId").asText()).isEqualTo("export-1");
        assertThat(item.path("boardId").asText()).isEqualTo("realestate");
        assertThat(item.path("title").asText()).isEqualTo("파주시 GTX 기대와 전세 우려가 같이 언급됨");
        assertThat(item.path("contentSnippet").asText()).isEqualTo("운정 신축과 교통 이슈가 함께 언급됨");
        assertThat(item.path("publishedAt").asText()).isEqualTo("2026-06-14T00:31:00Z");
        assertThat(item.path("viewCount").asInt()).isEqualTo(120);
        assertThat(item.path("recommendCount").asInt()).isEqualTo(4);
        assertThat(item.path("commentCount").asInt()).isEqualTo(9);
    }
}
