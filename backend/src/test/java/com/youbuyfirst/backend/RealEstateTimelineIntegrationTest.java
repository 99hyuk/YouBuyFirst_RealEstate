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
class RealEstateTimelineIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void upsertsPolicyEventsAndMaterializesApprovedTargetTimeline() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("eventId", "policy-20260612-supply"),
                        Map.entry("eventType", "supply"),
                        Map.entry("title", "서울 도심 공급 대책 발표"),
                        Map.entry("summary", "도심 공급 확대 후보지가 공개되어 관련 지역 관심이 늘 수 있습니다."),
                        Map.entry("sourceUrl", "https://example.gov/policy/20260612"),
                        Map.entry("publishedAt", "2026-06-12T00:30:00Z"),
                        Map.entry("effectiveFrom", "2026-07-01T00:00:00Z"),
                        Map.entry("effectiveTo", "2026-12-31T00:00:00Z"),
                        Map.entry("targetScope", "sigungu"),
                        Map.entry("dataStatus", "ok"),
                        Map.entry("targets", List.of(
                                Map.of(
                                        "targetId", "region-seoul-jongno",
                                        "impactType", "direct",
                                        "confidence", 0.82,
                                        "reviewState", "approved"
                                ),
                                Map.of(
                                        "targetId", "region-seoul",
                                        "impactType", "context",
                                        "confidence", 0.50,
                                        "reviewState", "candidate"
                                )
                        ))
                ))
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/policy-events",
                request,
                String.class
        );
        ResponseEntity<String> approvedTimeline = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/timeline?eventType=supply&limit=10",
                String.class,
                "region-seoul-jongno"
        );
        ResponseEntity<String> candidateTimeline = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/timeline?eventType=supply&limit=10",
                String.class,
                "region-seoul"
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode ingestRoot = objectMapper.readTree(ingest.getBody());
        assertThat(ingestRoot.path("acceptedEvents").asInt()).isEqualTo(1);
        assertThat(ingestRoot.path("acceptedTargetLinks").asInt()).isEqualTo(2);
        assertThat(ingestRoot.path("materializedTimelineEvents").asInt()).isEqualTo(1);

        assertThat(approvedTimeline.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(approvedTimeline.getBody()).path("items");
        assertThat(items).hasSize(1);
        JsonNode event = items.get(0);
        assertThat(event.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(event.path("eventType").asText()).isEqualTo("supply");
        assertThat(event.path("sourceRefType").asText()).isEqualTo("policy_event");
        assertThat(event.path("sourceRefId").asText()).isEqualTo("policy-20260612-supply");
        assertThat(event.path("title").asText()).isEqualTo("서울 도심 공급 대책 발표");
        assertThat(event.path("summary").asText()).contains("공급 확대 후보지");
        assertThat(event.path("occurredAt").asText()).isEqualTo("2026-06-12T00:30:00Z");
        assertThat(event.path("asOf").asText()).isEqualTo("2026-06-12T00:30:00Z");
        assertThat(event.path("dataStatus").asText()).isEqualTo("ok");

        assertThat(candidateTimeline.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(objectMapper.readTree(candidateTimeline.getBody()).path("items")).isEmpty();
    }

    @Test
    void marketFactIngestMaterializesTargetTimelineEvent() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetType", "region"),
                        Map.entry("targetId", "region-seoul-jongno"),
                        Map.entry("factType", "apt_trade"),
                        Map.entry("provider", "molit"),
                        Map.entry("providerDataset", "molit_apt_trade"),
                        Map.entry("providerObjectId", "molit_apt_trade:11110:202606:timeline-detail"),
                        Map.entry("legalDongCode", "11110"),
                        Map.entry("observedAt", "2026-06-12"),
                        Map.entry("asOf", "2026-06-01"),
                        Map.entry("ingestedAt", "2026-06-12T01:20:00Z"),
                        Map.entry("sourceUpdatedAt", "2026-06-12T01:00:00Z"),
                        Map.entry("dataStatus", "ok"),
                        Map.entry("stale", false),
                        Map.entry("valueJson", Map.of(
                                "apartmentName", "Timeline Palace",
                                "dealAmountManwon", 92600,
                                "exclusiveAreaM2", 84.97
                        ))
                ))
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                request,
                String.class
        );
        ResponseEntity<String> timeline = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/timeline?eventType=market_fact&limit=10",
                String.class,
                "region-seoul-jongno"
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(timeline.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(timeline.getBody()).path("items");
        assertThat(items.size()).isGreaterThanOrEqualTo(1);
        JsonNode event = findTimelineEvent(items, "Timeline Palace", "9.26억원");
        assertThat(event).isNotNull();
        assertThat(event.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(event.path("eventType").asText()).isEqualTo("market_fact");
        assertThat(event.path("sourceRefType").asText()).isEqualTo("market_fact");
        assertThat(event.path("sourceRefId").asText()).isNotBlank();
        assertThat(event.path("title").asText()).isEqualTo("매매 실거래");
        assertThat(event.path("summary").asText()).contains("Timeline Palace", "9.26억원");
        assertThat(event.path("occurredAt").asText()).isEqualTo("2026-06-12T00:00:00Z");
        assertThat(event.path("asOf").asText()).isEqualTo("2026-06-01T00:00:00Z");
        assertThat(event.path("dataStatus").asText()).isEqualTo("ok");
    }

    @Test
    void reactionSnapshotIngestMaterializesTargetTimelineEvent() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetType", "region"),
                        Map.entry("targetId", "region-seoul-jongno"),
                        Map.entry("windowStart", "2026-06-12T02:00:00Z"),
                        Map.entry("windowEnd", "2026-06-12T03:00:00Z"),
                        Map.entry("asOf", "2026-06-12T03:02:00Z"),
                        Map.entry("mentionCount", 210),
                        Map.entry("previousMentionCount", 120),
                        Map.entry("expectationScore", 88),
                        Map.entry("concernScore", 52),
                        Map.entry("neutralScore", 20),
                        Map.entry("heatScore", 91),
                        Map.entry("confidence", 0.81),
                        Map.entry("sourceCount", 5),
                        Map.entry("sourceSkew", 0.38),
                        Map.entry("coverageStatus", "partial"),
                        Map.entry("stale", false),
                        Map.entry("issues", List.of(
                                Map.of(
                                        "issueKey", "subscription",
                                        "label", "청약",
                                        "share", 0.36,
                                        "direction", "expectation",
                                        "summary", "청약 기대와 분양 일정 언급이 같이 늘었습니다.",
                                        "confidence", 0.77
                                ),
                                Map.of(
                                        "issueKey", "loan",
                                        "label", "대출",
                                        "share", 0.22,
                                        "direction", "concern",
                                        "summary", "대출 부담 우려도 일부 남아 있습니다.",
                                        "confidence", 0.69
                                )
                        ))
                ))
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                request,
                String.class
        );
        ResponseEntity<String> timeline = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/timeline?eventType=reaction&limit=10",
                String.class,
                "region-seoul-jongno"
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(timeline.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(timeline.getBody()).path("items");
        assertThat(items.size()).isGreaterThanOrEqualTo(1);
        JsonNode event = findTimelineEvent(items, "언급 210건", "+75.0%");
        assertThat(event).isNotNull();
        assertThat(event.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(event.path("eventType").asText()).isEqualTo("reaction");
        assertThat(event.path("sourceRefType").asText()).isEqualTo("reaction_snapshot");
        assertThat(event.path("sourceRefId").asText()).isNotBlank();
        assertThat(event.path("title").asText()).isEqualTo("커뮤니티 기대 우세");
        assertThat(event.path("summary").asText()).contains("청약", "대출");
        assertThat(event.path("occurredAt").asText()).isEqualTo("2026-06-12T03:00:00Z");
        assertThat(event.path("asOf").asText()).isEqualTo("2026-06-12T03:02:00Z");
        assertThat(event.path("dataStatus").asText()).isEqualTo("partial");
    }

    private static JsonNode findTimelineEvent(JsonNode items, String firstMarker, String secondMarker) {
        for (JsonNode item : items) {
            String summary = item.path("summary").asText();
            if (summary.contains(firstMarker) && summary.contains(secondMarker)) {
                return item;
            }
        }
        return null;
    }
}
