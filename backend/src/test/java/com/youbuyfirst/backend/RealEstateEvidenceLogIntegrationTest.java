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
class RealEstateEvidenceLogIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void upsertsEvidenceLogWithItemsAndListsLatestTargetLogs() throws Exception {
        Map<String, Object> request = Map.of(
                "logs",
                List.of(Map.ofEntries(
                        Map.entry("evidenceLogId", "evidence-region-seoul-jongno-20260612"),
                        Map.entry("targetId", "region-seoul-jongno"),
                        Map.entry("evaluationVersion", "realestate-eval-v1"),
                        Map.entry("promptVersion", "realestate-eval-prompt-v1"),
                        Map.entry("modelName", "gpt-4.1-mini"),
                        Map.entry("tone", "watch"),
                        Map.entry("summary", "전세 우려와 교통 기대가 함께 관찰됩니다."),
                        Map.entry("subtitle", "반응 지표와 검색 후보를 함께 본 후보 평가"),
                        Map.entry("caveats", List.of("search_candidate_unapproved", "market_fact_partial")),
                        Map.entry("dataQuality", "partial"),
                        Map.entry("confidence", 0.72),
                        Map.entry("evaluatedAt", "2026-06-12T01:40:00Z"),
                        Map.entry("asOf", "2026-06-12T01:40:00Z"),
                        Map.entry("skipReason", ""),
                        Map.entry("evidenceItems", List.of(
                                Map.of(
                                        "evidenceItemId", "evidence-item-reaction-1",
                                        "evidenceType", "reaction",
                                        "refType", "reaction_snapshot",
                                        "refId", "snapshot-region-seoul-jongno-20260612",
                                        "label", "언급 증가",
                                        "valueText", "+38%",
                                        "severity", "watch"
                                ),
                                Map.of(
                                        "evidenceItemId", "evidence-item-search-1",
                                        "evidenceType", "content",
                                        "refType", "content",
                                        "refId", "serpapi-issue-example",
                                        "label", "최근 이슈 후보",
                                        "valueText", "교통 관련 기사 후보",
                                        "severity", "info"
                                )
                        ))
                ))
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/evidence-logs",
                request,
                String.class
        );
        ResponseEntity<String> targetLogs = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/evidence-logs?limit=10",
                String.class,
                "region-seoul-jongno"
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode ingestRoot = objectMapper.readTree(ingest.getBody());
        assertThat(ingestRoot.path("acceptedLogs").asInt()).isEqualTo(1);
        assertThat(ingestRoot.path("acceptedItems").asInt()).isEqualTo(2);

        assertThat(targetLogs.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode logs = objectMapper.readTree(targetLogs.getBody()).path("items");
        assertThat(logs).hasSize(1);
        JsonNode log = logs.get(0);
        assertThat(log.path("evidenceLogId").asText()).isEqualTo("evidence-region-seoul-jongno-20260612");
        assertThat(log.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(log.path("evaluationVersion").asText()).isEqualTo("realestate-eval-v1");
        assertThat(log.path("promptVersion").asText()).isEqualTo("realestate-eval-prompt-v1");
        assertThat(log.path("modelName").asText()).isEqualTo("gpt-4.1-mini");
        assertThat(log.path("tone").asText()).isEqualTo("watch");
        assertThat(log.path("summary").asText()).contains("전세 우려");
        assertThat(log.path("dataQuality").asText()).isEqualTo("partial");
        assertThat(log.path("confidence").asDouble()).isEqualTo(0.72);
        assertThat(log.path("skipReason").isNull()).isTrue();
        assertThat(log.path("caveats")).hasSize(2);

        JsonNode evidenceItems = log.path("evidenceItems");
        assertThat(evidenceItems).hasSize(2);
        assertThat(evidenceItems.get(0).path("evidenceType").asText()).isEqualTo("reaction");
        assertThat(evidenceItems.get(0).path("label").asText()).isEqualTo("언급 증가");
        assertThat(evidenceItems.get(1).path("refType").asText()).isEqualTo("content");
        assertThat(evidenceItems.get(1).path("severity").asText()).isEqualTo("info");
    }
}
