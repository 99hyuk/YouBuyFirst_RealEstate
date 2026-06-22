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
                                Map.entry("targetId", "region-seoul-mapo"),
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
                                Map.entry("targetId", "region-daejeon-yuseong"),
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
        ResponseEntity<String> scopedRanking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=region&windowStart=2026-06-13T00:00:00Z&windowMinutes=60&parentTargetId=region-seoul",
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
        assertThat(scopedRanking.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(targetSnapshot.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode root = objectMapper.readTree(ranking.getBody());
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

        JsonNode scopedItems = objectMapper.readTree(scopedRanking.getBody()).path("items");
        assertThat(scopedItems.findValuesAsText("targetId"))
                .containsExactly("region-seoul-jongno", "region-seoul-mapo");
    }

    @Test
    void latestRankingKeepsRequestedWindowSizeWhenNewerShortWindowExists() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-daejeon-yuseong"),
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
                                Map.entry("targetId", "region-busan-haeundae"),
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
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-gangnam"),
                                Map.entry("windowStart", "2026-06-15T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-16T00:00:00Z"),
                                Map.entry("asOf", "2026-06-15T00:03:00Z"),
                                Map.entry("mentionCount", 150),
                                Map.entry("previousMentionCount", 10),
                                Map.entry("expectationScore", 70),
                                Map.entry("concernScore", 20),
                                Map.entry("neutralScore", 60),
                                Map.entry("heatScore", 95),
                                Map.entry("confidence", 0.82),
                                Map.entry("sourceCount", 1),
                                Map.entry("sourceSkew", 1.0),
                                Map.entry("coverageStatus", "source_skewed"),
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
        assertThat(root.path("items").get(0).path("targetId").asText()).isEqualTo("region-daejeon-yuseong");
    }

    @Test
    void upsertMergesDuplicateIssueKeysWithinSnapshotPayload() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
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
                        "region-seoul-jongno",
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
                        "region-seoul-jongno",
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
    void complexRankingReturnsGlobalTopTenWithoutParentScope() throws Exception {
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
        ResponseEntity<String> complexRanking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=complex&windowStart=2026-06-14T00:00:00Z&windowMinutes=1440&limit=10",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(complexRanking.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode root = objectMapper.readTree(complexRanking.getBody());
        assertThat(root.path("items")).hasSize(2);
        assertThat(root.path("items").findValuesAsText("targetId"))
                .containsExactly("complex-dongtan-lotte-castle", "complex-mapo-raemian-prugio");
    }

    @Test
    void complexRankingIncludesComplexesRegisteredUnderNestedDongRegionsWithoutParentScope() throws Exception {
        String dongTargetId = "region-seoul-jongno-sajik-mvp";
        String complexTargetId = "complex-molit-1111011500-sajik-palace-mvp";
        Map<String, Object> regionRequest = Map.of(
                "items",
                List.of(Map.of(
                        "targetId", dongTargetId,
                        "displayName", "Sajik-dong",
                        "regionLevel", "eupmyeondong",
                        "parentTargetId", "region-seoul-jongno",
                        "legalDongCode", "1111011500",
                        "regionCode", "1111011500",
                        "source", "test"
                ))
        );
        Map<String, Object> targetRequest = Map.of(
                "items",
                List.of(Map.of(
                        "targetId", complexTargetId,
                        "targetType", "complex",
                        "displayName", "Sajik Palace MVP",
                        "slug", "molit-1111011500-sajik-palace-mvp",
                        "reviewState", "approved",
                        "dataStatus", "partial"
                ))
        );
        Map<String, Object> complexRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetId", complexTargetId),
                        Map.entry("regionTargetId", dongTargetId),
                        Map.entry("legalDongCode", "1111011500"),
                        Map.entry("jibunAddress", "Sajik-dong 1-1"),
                        Map.entry("source", "molit:market-fact"),
                        Map.entry("markerDataStatus", "partial"),
                        Map.entry("markerStale", true)
                ))
        );
        Map<String, Object> snapshotRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetType", "complex"),
                        Map.entry("targetId", complexTargetId),
                        Map.entry("windowStart", "2026-06-16T00:00:00Z"),
                        Map.entry("windowEnd", "2026-06-17T00:00:00Z"),
                        Map.entry("asOf", "2026-06-17T00:02:00Z"),
                        Map.entry("mentionCount", 66),
                        Map.entry("previousMentionCount", 12),
                        Map.entry("expectationScore", 38),
                        Map.entry("concernScore", 14),
                        Map.entry("neutralScore", 14),
                        Map.entry("heatScore", 79),
                        Map.entry("confidence", 0.76),
                        Map.entry("sourceCount", 3),
                        Map.entry("sourceSkew", 0.33),
                        Map.entry("coverageStatus", "partial"),
                        Map.entry("stale", false),
                        Map.entry("issues", List.of())
                ))
        );

        ResponseEntity<String> regionResponse = restTemplate.postForEntity(
                "/internal/realestate/regions",
                regionRequest,
                String.class
        );
        ResponseEntity<String> targetResponse = restTemplate.postForEntity(
                "/internal/realestate/targets",
                targetRequest,
                String.class
        );
        ResponseEntity<String> complexResponse = restTemplate.postForEntity(
                "/internal/realestate/complexes",
                complexRequest,
                String.class
        );
        ResponseEntity<String> snapshotResponse = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                snapshotRequest,
                String.class
        );
        ResponseEntity<String> complexRanking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=complex&windowStart=2026-06-16T00:00:00Z&windowMinutes=1440&limit=10",
                String.class
        );

        assertThat(regionResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(targetResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(complexResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(snapshotResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(complexRanking.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode root = objectMapper.readTree(complexRanking.getBody());
        assertThat(root.path("items").findValuesAsText("targetId"))
                .contains(complexTargetId);
    }

    @Test
    void complexRankingResolvesOfficialCommunityNamesToCanonicalTargets() throws Exception {
        String communityTargetId = "complex-community-ranking-canonical-match";
        String canonicalTargetId = "complex-test-ranking-canonical-match";
        String displayName = "Canonical Ranking Palace Official";
        Map<String, Object> communityTargetRequest = Map.of(
                "items",
                List.of(Map.of(
                        "targetId", communityTargetId,
                        "targetType", "complex",
                        "displayName", displayName,
                        "slug", "community-ranking-canonical-match",
                        "reviewState", "candidate",
                        "dataStatus", "community_observed"
                ))
        );
        Map<String, Object> communityComplexRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetId", communityTargetId),
                        Map.entry("regionTargetId", "region-seoul-jongno"),
                        Map.entry("legalDongCode", "1111010100"),
                        Map.entry("jibunAddress", "community observed address"),
                        Map.entry("source", "community:observed"),
                        Map.entry("coordinateStatus", "candidate"),
                        Map.entry("markerDataStatus", "community_observed"),
                        Map.entry("markerStale", true)
                ))
        );
        Map<String, Object> snapshotRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetType", "complex"),
                        Map.entry("targetId", communityTargetId),
                        Map.entry("windowStart", "2026-06-21T00:00:00Z"),
                        Map.entry("windowEnd", "2026-06-22T00:00:00Z"),
                        Map.entry("asOf", "2026-06-22T00:02:00Z"),
                        Map.entry("mentionCount", 54),
                        Map.entry("previousMentionCount", 18),
                        Map.entry("expectationScore", 30),
                        Map.entry("concernScore", 12),
                        Map.entry("neutralScore", 12),
                        Map.entry("heatScore", 81),
                        Map.entry("confidence", 0.74),
                        Map.entry("sourceCount", 3),
                        Map.entry("sourceSkew", 0.29),
                        Map.entry("coverageStatus", "partial"),
                        Map.entry("stale", false),
                        Map.entry("issues", List.of())
                ))
        );
        Map<String, Object> canonicalTargetRequest = Map.of(
                "items",
                List.of(Map.of(
                        "targetId", canonicalTargetId,
                        "targetType", "complex",
                        "displayName", displayName,
                        "slug", "ranking-canonical-match",
                        "reviewState", "approved",
                        "dataStatus", "ok"
                ))
        );
        Map<String, Object> canonicalComplexRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetId", canonicalTargetId),
                        Map.entry("regionTargetId", "region-seoul-jongno"),
                        Map.entry("legalDongCode", "1111010100"),
                        Map.entry("jibunAddress", "canonical ranking address"),
                        Map.entry("source", "ssafy_home:test"),
                        Map.entry("latitude", 37.5712),
                        Map.entry("longitude", 126.9823),
                        Map.entry("coordinateProvider", "ssafy_home:test"),
                        Map.entry("coordinateAsOf", "2026-06-16T00:00:00Z"),
                        Map.entry("coordinateStatus", "ok"),
                        Map.entry("markerDataStatus", "ok"),
                        Map.entry("markerStale", false)
                ))
        );

        ResponseEntity<String> communityTargetResponse = restTemplate.postForEntity(
                "/internal/realestate/targets",
                communityTargetRequest,
                String.class
        );
        ResponseEntity<String> communityComplexResponse = restTemplate.postForEntity(
                "/internal/realestate/complexes",
                communityComplexRequest,
                String.class
        );
        ResponseEntity<String> snapshotResponse = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                snapshotRequest,
                String.class
        );
        ResponseEntity<String> canonicalTargetResponse = restTemplate.postForEntity(
                "/internal/realestate/targets",
                canonicalTargetRequest,
                String.class
        );
        ResponseEntity<String> canonicalComplexResponse = restTemplate.postForEntity(
                "/internal/realestate/complexes",
                canonicalComplexRequest,
                String.class
        );
        ResponseEntity<String> ranking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=complex&windowStart=2026-06-21T00:00:00Z&windowMinutes=1440&limit=10",
                String.class
        );

        assertThat(communityTargetResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(communityComplexResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(snapshotResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(canonicalTargetResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(canonicalComplexResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ranking.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode root = objectMapper.readTree(ranking.getBody());
        JsonNode row = root.path("items").get(0);
        assertThat(row.path("targetId").asText()).isEqualTo(canonicalTargetId);
        assertThat(row.path("displayName").asText()).isEqualTo(displayName);
        assertThat(row.path("mentionCount").asInt()).isEqualTo(54);
        assertThat(root.path("items").findValuesAsText("targetId"))
                .doesNotContain(communityTargetId);
    }

    @Test
    void upsertMergesCommunityObservedAndApprovedComplexSnapshotsAfterCanonicalResolution() throws Exception {
        String communityTargetId = "complex-community-merge-canonical-match";
        String canonicalTargetId = "complex-test-merge-canonical-match";
        String displayName = "Canonical Merge Palace Official";
        Map<String, Object> communityTargetRequest = Map.of(
                "items",
                List.of(Map.of(
                        "targetId", communityTargetId,
                        "targetType", "complex",
                        "displayName", displayName,
                        "slug", "community-merge-canonical-match",
                        "reviewState", "candidate",
                        "dataStatus", "community_observed"
                ))
        );
        Map<String, Object> canonicalTargetRequest = Map.of(
                "items",
                List.of(Map.of(
                        "targetId", canonicalTargetId,
                        "targetType", "complex",
                        "displayName", displayName,
                        "slug", "merge-canonical-match",
                        "reviewState", "approved",
                        "dataStatus", "ok"
                ))
        );
        Map<String, Object> communityComplexRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetId", communityTargetId),
                        Map.entry("regionTargetId", "region-seoul-jongno"),
                        Map.entry("legalDongCode", "1111010100"),
                        Map.entry("jibunAddress", "community observed address"),
                        Map.entry("source", "community:observed"),
                        Map.entry("coordinateStatus", "candidate"),
                        Map.entry("markerDataStatus", "community_observed"),
                        Map.entry("markerStale", true)
                ))
        );
        Map<String, Object> canonicalComplexRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetId", canonicalTargetId),
                        Map.entry("regionTargetId", "region-seoul-jongno"),
                        Map.entry("legalDongCode", "1111010100"),
                        Map.entry("jibunAddress", "canonical merge address"),
                        Map.entry("source", "ssafy_home:test"),
                        Map.entry("latitude", 37.5712),
                        Map.entry("longitude", 126.9823),
                        Map.entry("coordinateProvider", "ssafy_home:test"),
                        Map.entry("coordinateAsOf", "2026-06-16T00:00:00Z"),
                        Map.entry("coordinateStatus", "ok"),
                        Map.entry("markerDataStatus", "ok"),
                        Map.entry("markerStale", false)
                ))
        );
        Map<String, Object> snapshotRequest = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "complex"),
                                Map.entry("targetId", communityTargetId),
                                Map.entry("windowStart", "2026-06-22T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-23T00:00:00Z"),
                                Map.entry("asOf", "2026-06-23T00:02:00Z"),
                                Map.entry("mentionCount", 20),
                                Map.entry("previousMentionCount", 5),
                                Map.entry("expectationScore", 12),
                                Map.entry("concernScore", 4),
                                Map.entry("neutralScore", 4),
                                Map.entry("heatScore", 71),
                                Map.entry("confidence", 0.70),
                                Map.entry("sourceCount", 2),
                                Map.entry("sourceSkew", 0.30),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of(Map.of(
                                        "issueKey", "policy",
                                        "label", "Policy",
                                        "share", 0.50,
                                        "direction", "concern",
                                        "summary", "Policy concern",
                                        "confidence", 0.70
                                )))
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "complex"),
                                Map.entry("targetId", canonicalTargetId),
                                Map.entry("windowStart", "2026-06-22T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-23T00:00:00Z"),
                                Map.entry("asOf", "2026-06-23T00:03:00Z"),
                                Map.entry("mentionCount", 30),
                                Map.entry("previousMentionCount", 7),
                                Map.entry("expectationScore", 18),
                                Map.entry("concernScore", 6),
                                Map.entry("neutralScore", 6),
                                Map.entry("heatScore", 77),
                                Map.entry("confidence", 0.80),
                                Map.entry("sourceCount", 3),
                                Map.entry("sourceSkew", 0.50),
                                Map.entry("coverageStatus", "complete"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of(Map.of(
                                        "issueKey", "transport",
                                        "label", "Transport",
                                        "share", 0.30,
                                        "direction", "expectation",
                                        "summary", "Transport expectation",
                                        "confidence", 0.72
                                )))
                        )
                )
        );

        assertThat(restTemplate.postForEntity("/internal/realestate/targets", canonicalTargetRequest, String.class).getStatusCode())
                .isEqualTo(HttpStatus.OK);
        assertThat(restTemplate.postForEntity("/internal/realestate/complexes", canonicalComplexRequest, String.class).getStatusCode())
                .isEqualTo(HttpStatus.OK);
        assertThat(restTemplate.postForEntity("/internal/realestate/targets", communityTargetRequest, String.class).getStatusCode())
                .isEqualTo(HttpStatus.OK);
        assertThat(restTemplate.postForEntity("/internal/realestate/complexes", communityComplexRequest, String.class).getStatusCode())
                .isEqualTo(HttpStatus.OK);
        ResponseEntity<String> snapshotResponse = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                snapshotRequest,
                String.class
        );
        ResponseEntity<String> ranking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=complex&windowStart=2026-06-22T00:00:00Z&windowMinutes=1440&limit=10",
                String.class
        );

        assertThat(snapshotResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(snapshotResponse.getBody()).contains("\"acceptedSnapshots\":2");
        assertThat(ranking.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode root = objectMapper.readTree(ranking.getBody());
        JsonNode row = root.path("items").get(0);
        assertThat(root.path("items")).hasSize(1);
        assertThat(row.path("targetId").asText()).isEqualTo(canonicalTargetId);
        assertThat(row.path("mentionCount").asInt()).isEqualTo(50);
        assertThat(row.path("confidence").asDouble()).isEqualTo(0.80);
        assertThat(row.path("sourceCount").asInt()).isEqualTo(5);
        assertThat(row.path("issueMix").findValuesAsText("issueKey"))
                .containsExactly("policy", "transport");
    }

    @Test
    void complexRankingExcludesGenericStandaloneBrandNames() throws Exception {
        ResponseEntity<String> targetUpsert = restTemplate.postForEntity(
                "/internal/realestate/targets",
                Map.of("items", List.of(
                        Map.of(
                                "targetId", "complex-generic-hillstate-ranking-test",
                                "targetType", "complex",
                                "displayName", "힐스테이트",
                                "slug", "generic-hillstate-ranking-test",
                                "reviewState", "approved",
                                "dataStatus", "ok"
                        ),
                        Map.of(
                                "targetId", "complex-specific-hillstate-ranking-test",
                                "targetType", "complex",
                                "displayName", "논현동 힐스테이트",
                                "slug", "specific-hillstate-ranking-test",
                                "reviewState", "approved",
                                "dataStatus", "ok"
                        )
                )),
                String.class
        );
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "complex"),
                                Map.entry("targetId", "complex-generic-hillstate-ranking-test"),
                                Map.entry("windowStart", "2026-06-18T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-19T00:00:00Z"),
                                Map.entry("asOf", "2026-06-19T00:02:00Z"),
                                Map.entry("mentionCount", 999),
                                Map.entry("previousMentionCount", 10),
                                Map.entry("expectationScore", 60),
                                Map.entry("concernScore", 20),
                                Map.entry("neutralScore", 20),
                                Map.entry("heatScore", 99),
                                Map.entry("confidence", 0.5),
                                Map.entry("sourceCount", 1),
                                Map.entry("sourceSkew", 1.0),
                                Map.entry("coverageStatus", "source_skewed"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of())
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "complex"),
                                Map.entry("targetId", "complex-specific-hillstate-ranking-test"),
                                Map.entry("windowStart", "2026-06-18T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-19T00:00:00Z"),
                                Map.entry("asOf", "2026-06-19T00:03:00Z"),
                                Map.entry("mentionCount", 12),
                                Map.entry("previousMentionCount", 4),
                                Map.entry("expectationScore", 5),
                                Map.entry("concernScore", 4),
                                Map.entry("neutralScore", 3),
                                Map.entry("heatScore", 40),
                                Map.entry("confidence", 0.71),
                                Map.entry("sourceCount", 2),
                                Map.entry("sourceSkew", 0.5),
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
        ResponseEntity<String> ranking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=complex&windowStart=2026-06-18T00:00:00Z&windowMinutes=1440&limit=10",
                String.class
        );

        assertThat(targetUpsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ranking.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode root = objectMapper.readTree(ranking.getBody());
        assertThat(root.path("items").findValuesAsText("targetId"))
                .contains("complex-specific-hillstate-ranking-test")
                .doesNotContain("complex-generic-hillstate-ranking-test");
    }

    @Test
    void complexRankingExcludesSingleSourceSkewedCandidatesFromPrimaryRanking() throws Exception {
        ResponseEntity<String> targetUpsert = restTemplate.postForEntity(
                "/internal/realestate/targets",
                Map.of("items", List.of(
                        Map.of(
                                "targetId", "complex-source-skewed-ranking-test",
                                "targetType", "complex",
                                "displayName", "Source Skewed Palace",
                                "slug", "source-skewed-ranking-test",
                                "reviewState", "approved",
                                "dataStatus", "ok"
                        ),
                        Map.of(
                                "targetId", "complex-qualified-ranking-test",
                                "targetType", "complex",
                                "displayName", "Qualified Palace",
                                "slug", "qualified-ranking-test",
                                "reviewState", "approved",
                                "dataStatus", "ok"
                        )
                )),
                String.class
        );
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "complex"),
                                Map.entry("targetId", "complex-source-skewed-ranking-test"),
                                Map.entry("windowStart", "2026-06-19T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-20T00:00:00Z"),
                                Map.entry("asOf", "2026-06-20T00:02:00Z"),
                                Map.entry("mentionCount", 200),
                                Map.entry("previousMentionCount", 0),
                                Map.entry("expectationScore", 80),
                                Map.entry("concernScore", 10),
                                Map.entry("neutralScore", 10),
                                Map.entry("heatScore", 100),
                                Map.entry("confidence", 0.92),
                                Map.entry("sourceCount", 1),
                                Map.entry("sourceSkew", 1.0),
                                Map.entry("coverageStatus", "source_skewed"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of())
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "complex"),
                                Map.entry("targetId", "complex-qualified-ranking-test"),
                                Map.entry("windowStart", "2026-06-19T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-20T00:00:00Z"),
                                Map.entry("asOf", "2026-06-20T00:03:00Z"),
                                Map.entry("mentionCount", 12),
                                Map.entry("previousMentionCount", 4),
                                Map.entry("expectationScore", 5),
                                Map.entry("concernScore", 4),
                                Map.entry("neutralScore", 3),
                                Map.entry("heatScore", 40),
                                Map.entry("confidence", 0.71),
                                Map.entry("sourceCount", 2),
                                Map.entry("sourceSkew", 0.5),
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
        ResponseEntity<String> ranking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=complex&windowStart=2026-06-19T00:00:00Z&windowMinutes=1440&limit=10",
                String.class
        );
        ResponseEntity<String> skewedTargetSnapshot = restTemplate.getForEntity(
                "/api/realestate/targets/complex-source-skewed-ranking-test/reaction-snapshot?windowStart=2026-06-19T00:00:00Z&windowMinutes=1440",
                String.class
        );

        assertThat(targetUpsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ranking.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(skewedTargetSnapshot.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode root = objectMapper.readTree(ranking.getBody());
        assertThat(root.path("items").findValuesAsText("targetId"))
                .contains("complex-qualified-ranking-test")
                .doesNotContain("complex-source-skewed-ranking-test");
        JsonNode snapshotRoot = objectMapper.readTree(skewedTargetSnapshot.getBody());
        assertThat(snapshotRoot.path("mentionCount").asInt()).isZero();
        assertThat(snapshotRoot.path("quality").path("coverageStatus").asText()).isEqualTo("empty");
    }

    @Test
    void rankingExcludesRejectedTargetsEvenWhenOldSnapshotExists() throws Exception {
        ResponseEntity<String> targetUpsert = restTemplate.postForEntity(
                "/internal/realestate/targets",
                Map.of("items", List.of(
                        Map.of(
                                "targetId", "complex-rejected-ranking-test",
                                "targetType", "complex",
                                "displayName", "Rejected Ranking Test",
                                "slug", "rejected-ranking-test",
                                "reviewState", "rejected",
                                "dataStatus", "community_observed"
                        )
                )),
                String.class
        );
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "complex"),
                                Map.entry("targetId", "complex-rejected-ranking-test"),
                                Map.entry("windowStart", "2026-06-20T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-21T00:00:00Z"),
                                Map.entry("asOf", "2026-06-20T01:02:00Z"),
                                Map.entry("mentionCount", 999),
                                Map.entry("previousMentionCount", 1),
                                Map.entry("expectationScore", 60),
                                Map.entry("concernScore", 20),
                                Map.entry("neutralScore", 20),
                                Map.entry("heatScore", 99),
                                Map.entry("confidence", 0.5),
                                Map.entry("sourceCount", 1),
                                Map.entry("sourceSkew", 1.0),
                                Map.entry("coverageStatus", "low_sample"),
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
        ResponseEntity<String> ranking = restTemplate.getForEntity(
                "/api/realestate/reactions/rankings?type=complex&windowStart=2026-06-20T00:00:00Z&windowMinutes=1440&limit=10",
                String.class
        );

        assertThat(targetUpsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(ranking.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode root = objectMapper.readTree(ranking.getBody());
        assertThat(root.path("items")).isEmpty();
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
