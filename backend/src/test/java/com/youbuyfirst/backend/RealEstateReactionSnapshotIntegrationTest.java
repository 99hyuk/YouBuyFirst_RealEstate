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
class RealEstateReactionSnapshotIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void upsertsReactionSnapshotsAndRanksTargetsForRegionReactionScreen() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("windowStart", "2026-06-11T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-11T01:00:00Z"),
                                Map.entry("asOf", "2026-06-11T01:02:00Z"),
                                Map.entry("mentionCount", 128),
                                Map.entry("previousMentionCount", 88),
                                Map.entry("expectationScore", 57),
                                Map.entry("concernScore", 25),
                                Map.entry("neutralScore", 18),
                                Map.entry("heatScore", 82),
                                Map.entry("confidence", 0.78),
                                Map.entry("sourceCount", 4),
                                Map.entry("sourceSkew", 0.42),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of(
                                        Map.of(
                                                "issueKey", "jeonse",
                                                "label", "전세",
                                                "share", 0.41,
                                                "direction", "concern",
                                                "summary", "전세 매물과 가격 부담 언급이 같이 늘었습니다.",
                                                "confidence", 0.82
                                        ),
                                        Map.of(
                                                "issueKey", "school",
                                                "label", "학군",
                                                "share", 0.24,
                                                "direction", "expectation",
                                                "summary", "학군 선호와 실거주 기대가 반복됩니다.",
                                                "confidence", 0.71
                                        )
                                ))
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul"),
                                Map.entry("windowStart", "2026-06-11T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-11T01:00:00Z"),
                                Map.entry("asOf", "2026-06-11T01:01:00Z"),
                                Map.entry("mentionCount", 45),
                                Map.entry("previousMentionCount", 50),
                                Map.entry("expectationScore", 20),
                                Map.entry("concernScore", 15),
                                Map.entry("neutralScore", 10),
                                Map.entry("heatScore", 48),
                                Map.entry("confidence", 0.61),
                                Map.entry("sourceCount", 2),
                                Map.entry("sourceSkew", 0.55),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", true),
                                Map.entry("issues", List.of(
                                        Map.of(
                                                "issueKey", "policy",
                                                "label", "정책",
                                                "share", 0.33,
                                                "direction", "concern",
                                                "summary", "대출 규제 관망 반응이 남아 있습니다.",
                                                "confidence", 0.66
                                        )
                                ))
                        )
                )
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                request,
                String.class
        );
        ResponseEntity<String> ranking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=region&windowStart=2026-06-11T00:00:00Z&windowMinutes=60",
                String.class
        );
        ResponseEntity<String> latestRanking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=region&windowMinutes=60",
                String.class
        );
        ResponseEntity<String> targetSnapshot = restTemplate.getForEntity(
                "/api/realestate/targets/region-seoul-jongno/reaction-snapshot?windowMinutes=60",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ingest.getBody()).contains("\"acceptedSnapshots\":2");
        assertThat(ranking.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(latestRanking.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(targetSnapshot.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode root = objectMapper.readTree(ranking.getBody());
        JsonNode latestRoot = objectMapper.readTree(latestRanking.getBody());
        JsonNode targetRoot = objectMapper.readTree(targetSnapshot.getBody());
        assertThat(root.path("window").asText()).isEqualTo("60m");
        assertThat(latestRoot.path("windowStart").asText()).isEqualTo("2026-06-11T00:00:00Z");
        assertThat(root.path("windowStart").asText()).isEqualTo("2026-06-11T00:00:00Z");
        assertThat(root.path("windowEnd").asText()).isEqualTo("2026-06-11T01:00:00Z");
        assertThat(root.path("freshness").path("asOf").asText()).isEqualTo("2026-06-11T01:02:00Z");
        assertThat(root.path("freshness").path("staleCount").asInt()).isEqualTo(1);

        JsonNode items = root.path("items");
        assertThat(items).hasSize(2);
        JsonNode first = items.get(0);
        assertThat(first.path("rank").asInt()).isEqualTo(1);
        assertThat(first.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(first.path("targetType").asText()).isEqualTo("region");
        assertThat(first.path("displayName").asText()).isEqualTo("서울 종로구");
        assertThat(first.path("mentionCount").asInt()).isEqualTo(128);
        assertThat(first.path("mentionDeltaPct").asDouble()).isEqualTo(45.5);
        assertThat(first.path("reactionDirectionRatio").path("expectation").asDouble()).isEqualTo(0.57);
        assertThat(first.path("reactionDirectionRatio").path("concern").asDouble()).isEqualTo(0.25);
        assertThat(first.path("reactionDirectionRatio").path("neutral").asDouble()).isEqualTo(0.18);
        assertThat(first.path("heatScore").asInt()).isEqualTo(82);
        assertThat(first.path("confidence").asDouble()).isEqualTo(0.78);
        assertThat(first.path("sourceCount").asInt()).isEqualTo(4);
        assertThat(first.path("sourceSkew").asDouble()).isEqualTo(0.42);
        assertThat(first.path("coverageStatus").asText()).isEqualTo("partial");
        assertThat(first.path("stale").asBoolean()).isFalse();
        assertThat(first.path("issueMix").get(0).path("label").asText()).isEqualTo("전세");
        assertThat(first.path("issueMix").get(0).path("direction").asText()).isEqualTo("concern");

        assertThat(targetRoot.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(targetRoot.path("targetType").asText()).isEqualTo("region");
        assertThat(targetRoot.path("displayName").asText()).isEqualTo("서울 종로구");
        assertThat(targetRoot.path("window").asText()).isEqualTo("60m");
        assertThat(targetRoot.path("windowStart").asText()).isEqualTo("2026-06-11T00:00:00Z");
        assertThat(targetRoot.path("windowEnd").asText()).isEqualTo("2026-06-11T01:00:00Z");
        assertThat(targetRoot.path("mentionCount").asInt()).isEqualTo(128);
        assertThat(targetRoot.path("previousMentionCount").asInt()).isEqualTo(88);
        assertThat(targetRoot.path("mentionDeltaPct").asDouble()).isEqualTo(45.5);
        assertThat(targetRoot.path("dominantDirection").asText()).isEqualTo("expectation");
        assertThat(targetRoot.path("reactionDirectionRatio").path("expectation").asDouble()).isEqualTo(0.57);
        assertThat(targetRoot.path("quality").path("confidence").asDouble()).isEqualTo(0.78);
        assertThat(targetRoot.path("quality").path("sourceCount").asInt()).isEqualTo(4);
        assertThat(targetRoot.path("quality").path("sourceSkew").asDouble()).isEqualTo(0.42);
        assertThat(targetRoot.path("quality").path("coverageStatus").asText()).isEqualTo("partial");
        assertThat(targetRoot.path("quality").path("stale").asBoolean()).isFalse();
        assertThat(targetRoot.path("freshness").path("source").asText()).isEqualTo("real_estate_reaction_snapshots");
        assertThat(targetRoot.path("freshness").path("asOf").asText()).isEqualTo("2026-06-11T01:02:00Z");
        assertThat(targetRoot.path("freshness").path("staleCount").asInt()).isZero();
        assertThat(targetRoot.path("issueMix")).hasSize(2);
        assertThat(targetRoot.path("issueMix").get(0).path("issueKey").asText()).isEqualTo("jeonse");
    }
}
