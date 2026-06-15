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
                                Map.entry("windowStart", "2026-06-13T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-13T01:00:00Z"),
                                Map.entry("asOf", "2026-06-13T01:02:00Z"),
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
                                Map.entry("windowStart", "2026-06-13T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-13T01:00:00Z"),
                                Map.entry("asOf", "2026-06-13T01:01:00Z"),
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
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-daejeon"),
                                Map.entry("windowStart", "2026-06-13T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-13T01:00:00Z"),
                                Map.entry("asOf", "2026-06-13T01:03:00Z"),
                                Map.entry("mentionCount", 96),
                                Map.entry("previousMentionCount", 70),
                                Map.entry("expectationScore", 38),
                                Map.entry("concernScore", 32),
                                Map.entry("neutralScore", 26),
                                Map.entry("heatScore", 64),
                                Map.entry("confidence", 0.69),
                                Map.entry("sourceCount", 3),
                                Map.entry("sourceSkew", 0.48),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of(
                                        Map.of(
                                                "issueKey", "traffic",
                                                "label", "교통",
                                                "share", 0.29,
                                                "direction", "expectation",
                                                "summary", "교통 호재 후보 언급이 늘었습니다.",
                                                "confidence", 0.64
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
                "/api/realestate/reactions/rankings?type=region&windowStart=2026-06-13T00:00:00Z&windowMinutes=60",
                String.class
        );
        ResponseEntity<String> latestRanking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=region&windowMinutes=60",
                String.class
        );
        ResponseEntity<String> seoulRanking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=region&windowStart=2026-06-13T00:00:00Z&windowMinutes=60&parentTargetId=region-seoul&limit=10",
                String.class
        );
        ResponseEntity<String> targetSnapshot = restTemplate.getForEntity(
                "/api/realestate/targets/region-seoul-jongno/reaction-snapshot?windowMinutes=60",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ingest.getBody()).contains("\"acceptedSnapshots\":3");
        assertThat(ranking.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(latestRanking.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(seoulRanking.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(targetSnapshot.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode root = objectMapper.readTree(ranking.getBody());
        JsonNode seoulRoot = objectMapper.readTree(seoulRanking.getBody());
        JsonNode targetRoot = objectMapper.readTree(targetSnapshot.getBody());
        assertThat(root.path("window").asText()).isEqualTo("60m");
        assertThat(root.path("windowStart").asText()).isEqualTo("2026-06-13T00:00:00Z");
        assertThat(root.path("windowEnd").asText()).isEqualTo("2026-06-13T01:00:00Z");
        assertThat(root.path("freshness").path("asOf").asText()).isEqualTo("2026-06-13T01:03:00Z");
        assertThat(root.path("freshness").path("staleCount").asInt()).isEqualTo(1);

        JsonNode items = root.path("items");
        assertThat(items).hasSize(3);
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

        assertThat(seoulRoot.path("items")).hasSize(2);
        assertThat(seoulRoot.path("items").findValuesAsText("targetId"))
                .containsExactly("region-seoul-jongno", "region-seoul");
        assertThat(seoulRoot.path("items").findValuesAsText("targetId"))
                .doesNotContain("region-daejeon");

        assertThat(targetRoot.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(targetRoot.path("targetType").asText()).isEqualTo("region");
        assertThat(targetRoot.path("displayName").asText()).isEqualTo("서울 종로구");
        assertThat(targetRoot.path("window").asText()).isEqualTo("60m");
        assertThat(targetRoot.path("windowStart").asText()).isEqualTo("2026-06-13T00:00:00Z");
        assertThat(targetRoot.path("windowEnd").asText()).isEqualTo("2026-06-13T01:00:00Z");
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
        assertThat(targetRoot.path("freshness").path("asOf").asText()).isEqualTo("2026-06-13T01:02:00Z");
        assertThat(targetRoot.path("freshness").path("staleCount").asInt()).isZero();
        assertThat(targetRoot.path("issueMix")).hasSize(2);
        assertThat(targetRoot.path("issueMix").get(0).path("issueKey").asText()).isEqualTo("jeonse");
    }

    @Test
    void latestRankingKeepsRequestedWindowSizeWhenNewerShortWindowExists() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-daejeon"),
                                Map.entry("windowStart", "2026-06-14T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-15T00:00:00Z"),
                                Map.entry("asOf", "2026-06-15T00:03:00Z"),
                                Map.entry("mentionCount", 77),
                                Map.entry("previousMentionCount", 12),
                                Map.entry("expectationScore", 30),
                                Map.entry("concernScore", 20),
                                Map.entry("neutralScore", 27),
                                Map.entry("heatScore", 70),
                                Map.entry("confidence", 0.72),
                                Map.entry("sourceCount", 2),
                                Map.entry("sourceSkew", 0.4),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of())
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-busan"),
                                Map.entry("windowStart", "2026-06-15T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-15T01:00:00Z"),
                                Map.entry("asOf", "2026-06-15T01:03:00Z"),
                                Map.entry("mentionCount", 99),
                                Map.entry("previousMentionCount", 3),
                                Map.entry("expectationScore", 40),
                                Map.entry("concernScore", 20),
                                Map.entry("neutralScore", 39),
                                Map.entry("heatScore", 75),
                                Map.entry("confidence", 0.75),
                                Map.entry("sourceCount", 2),
                                Map.entry("sourceSkew", 0.4),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of())
                        )
                )
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                request,
                String.class
        );
        ResponseEntity<String> dailyRanking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=region&windowMinutes=1440&limit=10",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(dailyRanking.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode root = objectMapper.readTree(dailyRanking.getBody());
        assertThat(root.path("window").asText()).isEqualTo("1440m");
        assertThat(root.path("windowStart").asText()).isEqualTo("2026-06-14T00:00:00Z");
        assertThat(root.path("windowEnd").asText()).isEqualTo("2026-06-15T00:00:00Z");
        assertThat(root.path("items")).hasSize(1);
        assertThat(root.path("items").get(0).path("targetId").asText()).isEqualTo("region-daejeon");
    }

    @Test
    void upsertMergesDuplicateIssueKeysWithinSnapshotPayload() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul"),
                                Map.entry("windowStart", "2026-06-12T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-13T00:00:00Z"),
                                Map.entry("asOf", "2026-06-13T00:03:00Z"),
                                Map.entry("mentionCount", 12),
                                Map.entry("previousMentionCount", 8),
                                Map.entry("expectationScore", 4),
                                Map.entry("concernScore", 6),
                                Map.entry("neutralScore", 2),
                                Map.entry("heatScore", 42),
                                Map.entry("confidence", 0.64),
                                Map.entry("sourceCount", 2),
                                Map.entry("sourceSkew", 0.35),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of(
                                        Map.of(
                                                "issueKey", "jeonse",
                                                "label", "?꾩꽭",
                                                "share", 0.30,
                                                "direction", "concern",
                                                "summary", "?꾩꽭 遺덉븞 ?멸툒",
                                                "confidence", 0.70
                                        ),
                                        Map.of(
                                                "issueKey", "jeonse",
                                                "label", "?꾩꽭",
                                                "share", 0.20,
                                                "direction", "concern",
                                                "summary", "?꾩꽭 媛寃?遺???멸툒",
                                                "confidence", 0.68
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
                "/api/realestate/reactions/rankings?type=region&windowStart=2026-06-12T00:00:00Z&windowMinutes=1440",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ingest.getBody()).contains("\"acceptedSnapshots\":1");
        assertThat(ranking.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode issueMix = objectMapper.readTree(ranking.getBody()).path("items").get(0).path("issueMix");
        assertThat(issueMix).hasSize(1);
        assertThat(issueMix.get(0).path("issueKey").asText()).isEqualTo("jeonse");
        assertThat(issueMix.get(0).path("share").asDouble()).isEqualTo(0.50);
        assertThat(issueMix.get(0).path("confidence").asDouble()).isEqualTo(0.70);
    }

    @Test
    void upsertReplacesExistingIssuesWithoutUniqueKeyCollision() throws Exception {
        Map<String, Object> first = Map.of(
                "items",
                List.of(reactionSnapshotRequestWithIssues(
                        "region-seoul",
                        "2026-06-10T00:00:00Z",
                        "2026-06-11T00:00:00Z",
                        List.of(Map.of(
                                "issueKey", "jeonse",
                                "label", "?꾩꽭",
                                "share", 0.30,
                                "direction", "concern",
                                "summary", "?꾩꽭 遺덉븞 ?멸툒",
                                "confidence", 0.70
                        ))
                ))
        );
        Map<String, Object> second = Map.of(
                "items",
                List.of(reactionSnapshotRequestWithIssues(
                        "region-seoul",
                        "2026-06-10T00:00:00Z",
                        "2026-06-11T00:00:00Z",
                        List.of(
                                Map.of(
                                        "issueKey", "jeonse",
                                        "label", "?꾩꽭",
                                        "share", 0.55,
                                        "direction", "concern",
                                        "summary", "?꾩꽭 媛寃?遺???멸툒",
                                        "confidence", 0.81
                                ),
                                Map.of(
                                        "issueKey", "policy",
                                        "label", "?뺤콉",
                                        "share", 0.20,
                                        "direction", "concern",
                                        "summary", "?뺤콉 遺???멸툒",
                                        "confidence", 0.62
                                )
                        )
                ))
        );

        ResponseEntity<String> firstIngest = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                first,
                String.class
        );
        ResponseEntity<String> secondIngest = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                second,
                String.class
        );
        ResponseEntity<String> ranking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=region&windowStart=2026-06-10T00:00:00Z&windowMinutes=1440",
                String.class
        );

        assertThat(firstIngest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(secondIngest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ranking.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode issueMix = objectMapper.readTree(ranking.getBody()).path("items").get(0).path("issueMix");
        assertThat(issueMix).hasSize(2);
        assertThat(issueMix.get(0).path("issueKey").asText()).isEqualTo("jeonse");
        assertThat(issueMix.get(0).path("share").asDouble()).isEqualTo(0.55);
        assertThat(issueMix.get(0).path("confidence").asDouble()).isEqualTo(0.81);
    }

    @Test
    void parentScopedComplexRankingIncludesComplexesRegisteredUnderChildRegions() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "complex"),
                                Map.entry("targetId", "complex-mapo-raemian-prugio"),
                                Map.entry("windowStart", "2026-06-14T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-15T00:00:00Z"),
                                Map.entry("asOf", "2026-06-15T00:02:00Z"),
                                Map.entry("mentionCount", 88),
                                Map.entry("previousMentionCount", 40),
                                Map.entry("expectationScore", 42),
                                Map.entry("concernScore", 21),
                                Map.entry("neutralScore", 25),
                                Map.entry("heatScore", 77),
                                Map.entry("confidence", 0.73),
                                Map.entry("sourceCount", 3),
                                Map.entry("sourceSkew", 0.31),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of())
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "complex"),
                                Map.entry("targetId", "complex-dongtan-lotte-castle"),
                                Map.entry("windowStart", "2026-06-14T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-15T00:00:00Z"),
                                Map.entry("asOf", "2026-06-15T00:03:00Z"),
                                Map.entry("mentionCount", 91),
                                Map.entry("previousMentionCount", 52),
                                Map.entry("expectationScore", 39),
                                Map.entry("concernScore", 30),
                                Map.entry("neutralScore", 22),
                                Map.entry("heatScore", 74),
                                Map.entry("confidence", 0.7),
                                Map.entry("sourceCount", 2),
                                Map.entry("sourceSkew", 0.44),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of())
                        )
                )
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                request,
                String.class
        );
        ResponseEntity<String> seoulComplexRanking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=complex&windowMinutes=1440&parentTargetId=region-seoul&limit=10",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(seoulComplexRanking.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode root = objectMapper.readTree(seoulComplexRanking.getBody());
        assertThat(root.path("items")).hasSize(1);
        assertThat(root.path("items").get(0).path("targetId").asText()).isEqualTo("complex-mapo-raemian-prugio");
        assertThat(root.path("items").findValuesAsText("targetId"))
                .doesNotContain("complex-dongtan-lotte-castle");
    }

    private static Map<String, Object> reactionSnapshotRequestWithIssues(
            String targetId,
            String windowStart,
            String windowEnd,
            List<Map<String, Object>> issues
    ) {
        return Map.ofEntries(
                Map.entry("targetType", "region"),
                Map.entry("targetId", targetId),
                Map.entry("windowStart", windowStart),
                Map.entry("windowEnd", windowEnd),
                Map.entry("asOf", "2026-06-15T00:03:00Z"),
                Map.entry("mentionCount", 12),
                Map.entry("previousMentionCount", 8),
                Map.entry("expectationScore", 4),
                Map.entry("concernScore", 6),
                Map.entry("neutralScore", 2),
                Map.entry("heatScore", 42),
                Map.entry("confidence", 0.64),
                Map.entry("sourceCount", 2),
                Map.entry("sourceSkew", 0.35),
                Map.entry("coverageStatus", "partial"),
                Map.entry("stale", false),
                Map.entry("issues", issues)
        );
    }
}
