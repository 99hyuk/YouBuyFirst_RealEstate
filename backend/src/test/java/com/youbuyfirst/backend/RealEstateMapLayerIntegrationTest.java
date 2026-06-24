package com.youbuyfirst.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.realestate.batch.RealEstateBatchUpdatePublisher;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.annotation.DirtiesContext;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.verify;

@SpringBootTest(
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = "spring.datasource.url=jdbc:h2:mem:youbuyfirst_map_layer_test;MODE=MySQL;DATABASE_TO_LOWER=TRUE;CASE_INSENSITIVE_IDENTIFIERS=TRUE"
)
@ActiveProfiles("test")
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_EACH_TEST_METHOD)
class RealEstateMapLayerIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private RealEstateBatchUpdatePublisher batchUpdatePublisher;

    @Test
    void omitsSeedOnlyNationwideSidoMapLayerSnapshotsFromPriceMapApi() throws Exception {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sido",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.path("layerType").asText()).isEqualTo("sido");
        assertThat(body.path("dataStatus").asText()).isEqualTo("empty");
        assertThat(body.path("stale").asBoolean()).isFalse();
        assertThat(body.path("asOf").isNull()).isTrue();
        assertThat(body.path("periods"))
                .extracting(JsonNode::asText)
                .containsExactly("week", "month", "quarter", "halfYear", "year");
        assertThat(body.path("targets")).isEmpty();
    }

    @Test
    void omitsSeedOnlySigunguLayerForAParentRegionFromPriceMapApi() throws Exception {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.path("layerType").asText()).isEqualTo("sigungu");
        assertThat(body.path("parentTargetId").asText()).isEqualTo("region-seoul");
        assertThat(body.path("parentRegionCode").asText()).isEqualTo("11");
        assertThat(body.path("dataStatus").asText()).isEqualTo("empty");
        assertThat(body.path("targets")).isEmpty();
    }

    @Test
    void rejectsUnknownMapLayerInputWithoutServerError() {
        ResponseEntity<String> unsupportedLayer = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=unknown",
                String.class
        );
        ResponseEntity<String> unknownParent = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-unknown",
                String.class
        );

        assertThat(unsupportedLayer.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(unknownParent.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }

    @Test
    void refreshesSigunguMapLayerFromMarketFactsAndReactionSnapshots() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                mapFact("molit_apt_trade:11110:202606:map-refresh-before", "2026-06-03", 80000),
                                mapFact("molit_apt_trade:11110:202606:map-refresh-after", "2026-06-10", 88000)
                        )
                ),
                String.class
        );
        ResponseEntity<String> reactionSnapshots = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                Map.of(
                        "items",
                        List.of(Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("windowStart", "2026-06-10T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-10T01:00:00Z"),
                                Map.entry("asOf", "2026-06-10T01:02:00Z"),
                                Map.entry("mentionCount", 18),
                                Map.entry("previousMentionCount", 10),
                                Map.entry("expectationScore", 60),
                                Map.entry("concernScore", 25),
                                Map.entry("neutralScore", 15),
                                Map.entry("heatScore", 74),
                                Map.entry("confidence", 0.80),
                                Map.entry("sourceCount", 3),
                                Map.entry("sourceSkew", 0.30),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of(Map.of(
                                        "issueKey", "jeonse",
                                        "label", "전세",
                                        "share", 0.45,
                                        "direction", "concern",
                                        "summary", "전세와 가격 부담 언급이 함께 관찰됩니다.",
                                        "confidence", 0.72
                                )))
                        ))
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("month"),
                        "asOf", "2026-06-10T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(reactionSnapshots.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":1");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode jongno = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-seoul-jongno");
        assertThat(jongno).isNotNull();
        JsonNode month = jongno.path("periods").path("month");
        assertThat(month.path("changePct").asDouble()).isEqualTo(10.0);
        assertThat(month.path("sampleCount").asInt()).isEqualTo(2);
        assertThat(month.path("confidence").asDouble()).isEqualTo(80.0);
        assertThat(month.path("asOf").asText()).isEqualTo("2026-06-10T02:00:00Z");
        assertThat(month.path("provider").asText()).isEqualTo("real_estate_map_layer_refresh");
        assertThat(month.path("sourceLabel").asText()).contains("실거래", "반응 snapshot");
        assertThat(month.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(month.path("stale").asBoolean()).isFalse();
    }

    @Test
    void refreshPrefersStoredOfficialRebPriceIndexForMonthlyMapLayer() throws Exception {
        ResponseEntity<String> reactionSnapshots = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                Map.of(
                        "items",
                        List.of(Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("windowStart", "2026-06-15T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-16T00:00:00Z"),
                                Map.entry("asOf", "2026-06-15T02:00:00Z"),
                                Map.entry("mentionCount", 23),
                                Map.entry("previousMentionCount", 10),
                                Map.entry("expectationScore", 55),
                                Map.entry("concernScore", 25),
                                Map.entry("neutralScore", 20),
                                Map.entry("heatScore", 76),
                                Map.entry("confidence", 0.82),
                                Map.entry("sourceCount", 3),
                                Map.entry("sourceSkew", 0.20),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of())
                        ))
                ),
                String.class
        );
        ResponseEntity<String> partialRefresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("month"),
                        "asOf", "2026-06-15T03:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                mapFact("molit_apt_trade:11110:202605:official-priority-before", "2026-05-03", 80000),
                                mapFact("molit_apt_trade:11110:202605:official-priority-after", "2026-05-30", 96000),
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-04-01",
                                        100.0
                                ),
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-05-01",
                                        101.06
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("month"),
                        "asOf", "2026-06-10T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul",
                String.class
        );

        assertThat(reactionSnapshots.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(partialRefresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":1");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode jongno = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-seoul-jongno");
        assertThat(jongno).isNotNull();
        JsonNode month = jongno.path("periods").path("month");
        assertThat(month.path("changePct").asDouble()).isEqualTo(1.06);
        assertThat(month.path("sampleCount").asInt()).isEqualTo(2);
        assertThat(month.path("confidence").asDouble()).isEqualTo(100.0);
        assertThat(month.path("asOf").asText()).isEqualTo("2026-05-01T00:00:00Z");
        assertThat(month.path("provider").asText()).isEqualTo("reb");
        assertThat(month.path("sourceLabel").asText()).contains("R-ONE");
        assertThat(month.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(month.path("stale").asBoolean()).isFalse();
    }

    @Test
    void refreshComputesWeekAndMonthFromStoredOfficialRebPriceIndexFacts() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                weeklyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-06-20",
                                        100.0
                                ),
                                weeklyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-06-27",
                                        101.0
                                ),
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-04-01",
                                        100.0
                                ),
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-05-01",
                                        102.0
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("week", "month"),
                        "asOf", "2026-06-30T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":2");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode jongno = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-seoul-jongno");
        assertThat(jongno).isNotNull();

        JsonNode week = jongno.path("periods").path("week");
        assertThat(week.path("changePct").asDouble()).isEqualTo(1.0);
        assertThat(week.path("sampleCount").asInt()).isEqualTo(2);
        assertThat(week.path("provider").asText()).isEqualTo("reb");
        assertThat(week.path("sourceLabel").asText()).contains("weekly");
        assertThat(week.path("dataStatus").asText()).isEqualTo("ok");

        JsonNode month = jongno.path("periods").path("month");
        assertThat(month.path("changePct").asDouble()).isEqualTo(2.0);
        assertThat(month.path("sampleCount").asInt()).isEqualTo(2);
        assertThat(month.path("provider").asText()).isEqualTo("reb");
        assertThat(month.path("sourceLabel").asText()).contains("monthly");
        assertThat(month.path("dataStatus").asText()).isEqualTo("ok");
        verify(batchUpdatePublisher).publish(argThat(event ->
                "map-layers".equals(event.topic())
                        && event.acceptedItems() == 2
                        && event.month() == null
                && event.refreshedAt() != null
        ));
    }

    @Test
    void refreshComputesSejongSingleSigunguLayerFromStoredOfficialSidoPriceIndexFacts() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                monthlyPriceIndexFactAt(
                                        "region-sejong",
                                        "36",
                                        "2026-04-01",
                                        100.0
                                ),
                                monthlyPriceIndexFactAt(
                                        "region-sejong",
                                        "36",
                                        "2026-05-01",
                                        99.5
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("month"),
                        "asOf", "2026-05-31T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-sejong",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":1");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.path("parentRegionCode").asText()).isEqualTo("29");

        JsonNode sejongCity = findTarget(body.path("targets"), "region-sejong-sejongsi");
        assertThat(sejongCity).isNotNull();
        assertThat(sejongCity.path("regionCode").asText()).isEqualTo("29010");

        JsonNode month = sejongCity.path("periods").path("month");
        assertThat(month.path("changePct").asDouble()).isEqualTo(-0.5);
        assertThat(month.path("sampleCount").asInt()).isEqualTo(2);
        assertThat(month.path("provider").asText()).isEqualTo("reb");
        assertThat(month.path("sourceLabel").asText()).contains("monthly");
        assertThat(month.path("dataStatus").asText()).isEqualTo("ok");
    }

    @Test
    void refreshComputesSidoWeekFromRoneWeeklyProvinceCodeFacts() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                weeklyPriceIndexFactAt(
                                        null,
                                        "26000",
                                        "2026-06-20",
                                        100.0
                                ),
                                weeklyPriceIndexFactAt(
                                        null,
                                        "26000",
                                        "2026-06-27",
                                        101.5
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sido",
                        "periods", List.of("week"),
                        "asOf", "2026-06-30T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sido",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":1");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode busan = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-busan");
        assertThat(busan).isNotNull();
        JsonNode week = busan.path("periods").path("week");
        assertThat(week.path("changePct").asDouble()).isEqualTo(1.5);
        assertThat(week.path("provider").asText()).isEqualTo("reb");
        assertThat(week.path("dataStatus").asText()).isEqualTo("ok");
    }

    @Test
    void refreshComputesGangwonSigunguWeekFromLegacyRoneWeeklyCodeFacts() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                weeklyPriceIndexFactAt(
                                        null,
                                        "42110",
                                        "2026-06-20",
                                        100.0
                                ),
                                weeklyPriceIndexFactAt(
                                        null,
                                        "42110",
                                        "2026-06-27",
                                        102.0
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("week"),
                        "asOf", "2026-06-30T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-gangwon",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":1");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode chuncheon = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-gangwon-chuncheon");
        assertThat(chuncheon).isNotNull();
        JsonNode week = chuncheon.path("periods").path("week");
        assertThat(week.path("changePct").asDouble()).isEqualTo(2.0);
        assertThat(week.path("provider").asText()).isEqualTo("reb");
        assertThat(week.path("dataStatus").asText()).isEqualTo("ok");
    }

    @Test
    void refreshComputesDistrictWeekFromParentCityRoneWeeklyCodeFacts() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                weeklyPriceIndexFactAt(
                                        null,
                                        "41110",
                                        "2026-06-20",
                                        100.0
                                ),
                                weeklyPriceIndexFactAt(
                                        null,
                                        "41110",
                                        "2026-06-27",
                                        103.0
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("week"),
                        "asOf", "2026-06-30T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-gyeonggi",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":4");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode jangan = findTarget(
                objectMapper.readTree(response.getBody()).path("targets"),
                "region-gyeonggi-suwonsijangangu"
        );
        assertThat(jangan).isNotNull();
        JsonNode week = jangan.path("periods").path("week");
        assertThat(week.path("changePct").asDouble()).isEqualTo(3.0);
        assertThat(week.path("provider").asText()).isEqualTo("reb");
        assertThat(week.path("dataStatus").asText()).isEqualTo("ok");
    }

    @Test
    void refreshComputesJeonbukWeekFromLegacyRoneWeeklyCodeFacts() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                weeklyPriceIndexFactAt(
                                        null,
                                        "45130",
                                        "2026-06-20",
                                        100.0
                                ),
                                weeklyPriceIndexFactAt(
                                        null,
                                        "45130",
                                        "2026-06-27",
                                        98.0
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("week"),
                        "asOf", "2026-06-30T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-jeonbuk",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":1");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode gunsan = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-jeonbuk-gunsan");
        assertThat(gunsan).isNotNull();
        JsonNode week = gunsan.path("periods").path("week");
        assertThat(week.path("changePct").asDouble()).isEqualTo(-2.0);
        assertThat(week.path("provider").asText()).isEqualTo("reb");
        assertThat(week.path("dataStatus").asText()).isEqualTo("ok");
    }

    @Test
    void refreshComputesQuarterAndHalfYearFromStoredMonthlyRebPriceIndexFacts() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2025-11-01",
                                        100.0
                                ),
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2025-12-01",
                                        101.0
                                ),
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-01-01",
                                        102.0
                                ),
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-02-01",
                                        103.0
                                ),
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-03-01",
                                        104.0
                                ),
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-04-01",
                                        105.0
                                ),
                                monthlyPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "2026-05-01",
                                        106.0
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("quarter", "halfYear"),
                        "asOf", "2026-06-10T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":2");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode jongno = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-seoul-jongno");
        assertThat(jongno).isNotNull();

        JsonNode quarter = jongno.path("periods").path("quarter");
        assertThat(quarter.path("changePct").asDouble()).isEqualTo(2.9126);
        assertThat(quarter.path("sampleCount").asInt()).isEqualTo(4);
        assertThat(quarter.path("asOf").asText()).isEqualTo("2026-05-01T00:00:00Z");
        assertThat(quarter.path("provider").asText()).isEqualTo("reb");
        assertThat(quarter.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(quarter.path("stale").asBoolean()).isFalse();

        JsonNode halfYear = jongno.path("periods").path("halfYear");
        assertThat(halfYear.path("changePct").asDouble()).isEqualTo(6.0);
        assertThat(halfYear.path("sampleCount").asInt()).isEqualTo(7);
        assertThat(halfYear.path("provider").asText()).isEqualTo("reb");
        assertThat(halfYear.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(halfYear.path("stale").asBoolean()).isFalse();
    }

    @Test
    void refreshComputesMonthlyPeriodsFromStoredMonthlyRebPriceIndexFacts() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                monthlyPriceIndexFactAt(null, "11110", "2025-05-01", 100.0),
                                monthlyPriceIndexFactAt(null, "11110", "2025-06-01", 101.0),
                                monthlyPriceIndexFactAt(null, "11110", "2025-07-01", 102.0),
                                monthlyPriceIndexFactAt(null, "11110", "2025-08-01", 103.0),
                                monthlyPriceIndexFactAt(null, "11110", "2025-09-01", 104.0),
                                monthlyPriceIndexFactAt(null, "11110", "2025-10-01", 105.0),
                                monthlyPriceIndexFactAt(null, "11110", "2025-11-01", 106.0),
                                monthlyPriceIndexFactAt(null, "11110", "2025-12-01", 107.0),
                                monthlyPriceIndexFactAt(null, "11110", "2026-01-01", 108.0),
                                monthlyPriceIndexFactAt(null, "11110", "2026-02-01", 109.0),
                                monthlyPriceIndexFactAt(null, "11110", "2026-03-01", 110.0),
                                monthlyPriceIndexFactAt(null, "11110", "2026-04-01", 111.0),
                                monthlyPriceIndexFactAt(null, "11110", "2026-05-01", 112.0)
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("month", "quarter", "halfYear", "year"),
                        "asOf", "2026-06-10T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":4");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode jongno = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-seoul-jongno");
        assertThat(jongno).isNotNull();

        JsonNode month = jongno.path("periods").path("month");
        assertThat(month.path("changePct").asDouble()).isEqualTo(0.9009);
        assertThat(month.path("provider").asText()).isEqualTo("reb");
        assertThat(month.path("sourceLabel").asText()).contains("R-ONE");

        assertThat(jongno.path("periods").path("quarter").path("changePct").asDouble()).isEqualTo(2.7523);
        assertThat(jongno.path("periods").path("halfYear").path("changePct").asDouble()).isEqualTo(5.6604);
        assertThat(jongno.path("periods").path("year").path("changePct").asDouble()).isEqualTo(12.0);
    }

    @Test
    void refreshesSidoMapLayerFromChildSigunguMarketFacts() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                mapFactForTarget(
                                        "region-seoul-mapo",
                                        "11440",
                                        "molit_apt_trade:11440:202501:sido-before",
                                        "2025-01-04",
                                        70000
                                ),
                                mapFactForTarget(
                                        "region-seoul-mapo",
                                        "11440",
                                        "molit_apt_trade:11440:202501:sido-after",
                                        "2025-01-31",
                                        73500
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sido",
                        "periods", List.of("month"),
                        "asOf", "2025-01-31T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sido",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":1");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(body.path("stale").asBoolean()).isFalse();

        JsonNode seoul = findTarget(body.path("targets"), "region-seoul");
        assertThat(seoul).isNotNull();
        JsonNode month = seoul.path("periods").path("month");
        assertThat(month.path("changePct").asDouble()).isEqualTo(5.0);
        assertThat(month.path("sampleCount").asInt()).isEqualTo(2);
        assertThat(month.path("asOf").asText()).isEqualTo("2025-01-31T02:00:00Z");
        assertThat(month.path("provider").asText()).isEqualTo("real_estate_map_layer_refresh");
        assertThat(month.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(month.path("stale").asBoolean()).isFalse();
    }

    @Test
    void priceMapLayerDoesNotUseReactionOnlySnapshotWhenMarketFactsAreMissing() throws Exception {
        ResponseEntity<String> reactionSnapshots = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                Map.of(
                        "items",
                        List.of(Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul"),
                                Map.entry("windowStart", "2026-06-15T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-16T00:00:00Z"),
                                Map.entry("asOf", "2026-06-15T02:00:00Z"),
                                Map.entry("mentionCount", 21),
                                Map.entry("previousMentionCount", 10),
                                Map.entry("expectationScore", 50),
                                Map.entry("concernScore", 20),
                                Map.entry("neutralScore", 30),
                                Map.entry("heatScore", 71),
                                Map.entry("confidence", 0.86),
                                Map.entry("sourceCount", 3),
                                Map.entry("sourceSkew", 0.20),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of())
                        ))
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sido",
                        "periods", List.of("month"),
                        "asOf", "2026-06-15T03:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sido",
                String.class
        );

        assertThat(reactionSnapshots.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":0");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.path("dataStatus").asText()).isEqualTo("empty");
        assertThat(body.path("targets")).isEmpty();
    }

    @Test
    void refreshUsesLatestAvailableMarketFactWindowWhenCurrentWindowHasNoData() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                mapFactForTarget(
                                        "region-seoul-mapo",
                                        "11440",
                                        "molit_apt_trade:11440:202501:stale-window-before",
                                        "2025-01-04",
                                        70000
                                ),
                                mapFactForTarget(
                                        "region-seoul-mapo",
                                        "11440",
                                        "molit_apt_trade:11440:202501:stale-window-after",
                                        "2025-01-31",
                                        73500
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("month"),
                        "asOf", "2026-06-21T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode mapo = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-seoul-mapo");
        assertThat(mapo).isNotNull();
        JsonNode month = mapo.path("periods").path("month");
        assertThat(month.path("changePct").asDouble()).isEqualTo(5.0);
        assertThat(month.path("sampleCount").asInt()).isEqualTo(2);
        assertThat(month.path("asOf").asText()).isEqualTo("2025-01-31T00:00:00Z");
        assertThat(month.path("provider").asText()).isEqualTo("real_estate_map_layer_refresh");
        assertThat(month.path("dataStatus").asText()).isEqualTo("partial");
        assertThat(month.path("stale").asBoolean()).isTrue();
    }

    @Test
    void marksExtremeMapLayerChangeAsPartialInsteadOfNormalOk() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                mapFact("molit_apt_trade:11110:202701:extreme-before", "2027-01-02", 1000),
                                mapFact("molit_apt_trade:11110:202701:extreme-after", "2027-01-10", 200000)
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("month"),
                        "asOf", "2027-01-10T02:00:00Z"
                ),
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul",
                String.class
        );

        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":1");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode jongno = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-seoul-jongno");
        assertThat(jongno).isNotNull();
        JsonNode month = jongno.path("periods").path("month");
        assertThat(month.path("changePct").asDouble()).isEqualTo(19900.0);
        assertThat(month.path("dataStatus").asText()).isEqualTo("partial");
        assertThat(month.path("confidence").asDouble()).isEqualTo(10.0);
        assertThat(month.path("stale").asBoolean()).isTrue();
    }

    private static Map<String, Object> mapFact(String providerObjectId, String observedAt, int dealAmountManwon) {
        return mapFactForTarget("region-seoul-jongno", "11110", providerObjectId, observedAt, dealAmountManwon);
    }

    private static Map<String, Object> monthlyPriceIndexFactAt(
            String targetId,
            String legalDongCode,
            String observedAt,
            double indexValue
    ) {
        String periodKey = observedAt.substring(0, 7).replace("-", "");
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("targetType", "region");
        if (targetId != null) {
            item.put("targetId", targetId);
        }
        item.put("factType", "price_index");
        item.put("provider", "reb");
        item.put("providerDataset", "reb_rone_monthly_apt_sale_price_index");
        item.put("providerObjectId", "reb_rone_monthly_apt_sale_price_index:A_2024_00045:" + periodKey + ":" + legalDongCode);
        item.put("legalDongCode", legalDongCode);
        item.put("observedAt", observedAt);
        item.put("asOf", observedAt);
        item.put("ingestedAt", "2026-06-13T00:00:00Z");
        item.put("sourceUpdatedAt", "2026-06-13T00:00:00Z");
        item.put("dataStatus", "ok");
        item.put("stale", false);
        item.put("valueJson", Map.of(
                "regionName", "???",
                "metricName", "?????? ???",
                "housingType", "???",
                "surveyName", "??????????",
                "value", indexValue,
                "indexValue", indexValue,
                "unit", "지수",
                "sourceLabel", "REB R-ONE monthly apartment sale price index"
        ));
        return item;
    }

    private static Map<String, Object> weeklyPriceIndexFactAt(
            String targetId,
            String legalDongCode,
            String observedAt,
            double indexValue
    ) {
        String periodKey = observedAt.replace("-", "");
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("targetType", "region");
        if (targetId != null) {
            item.put("targetId", targetId);
        }
        item.put("factType", "price_index");
        item.put("provider", "reb");
        item.put("providerDataset", "reb_rone_weekly_apt_sale_price_index_region");
        item.put("providerObjectId", "reb_rone_weekly_apt_sale_price_index_region:A_2024_00016:" + periodKey + ":" + legalDongCode);
        item.put("legalDongCode", legalDongCode);
        item.put("observedAt", observedAt);
        item.put("asOf", observedAt);
        item.put("ingestedAt", "2026-06-30T00:00:00Z");
        item.put("sourceUpdatedAt", "2026-06-30T00:00:00Z");
        item.put("dataStatus", "ok");
        item.put("stale", false);
        item.put("valueJson", Map.of(
                "regionName", "서울 종로구",
                "metricName", "주간 아파트 매매가격지수",
                "housingType", "아파트",
                "surveyName", "전국주택가격동향조사",
                "value", indexValue,
                "indexValue", indexValue,
                "unit", "지수",
                "sourceLabel", "REB R-ONE weekly apartment sale price index"
        ));
        return item;
    }

    private static Map<String, Object> mapFactForTarget(
            String targetId,
            String legalDongCode,
            String providerObjectId,
            String observedAt,
            int dealAmountManwon
    ) {
        return Map.ofEntries(
                Map.entry("targetType", "region"),
                Map.entry("targetId", targetId),
                Map.entry("factType", "apt_trade"),
                Map.entry("provider", "molit"),
                Map.entry("providerDataset", "molit_apt_trade"),
                Map.entry("providerObjectId", providerObjectId),
                Map.entry("legalDongCode", legalDongCode),
                Map.entry("observedAt", observedAt),
                Map.entry("asOf", "2026-06-01"),
                Map.entry("ingestedAt", "2026-06-12T00:00:00Z"),
                Map.entry("sourceUpdatedAt", "2026-06-12T00:00:00Z"),
                Map.entry("dataStatus", "ok"),
                Map.entry("stale", false),
                Map.entry("valueJson", Map.of(
                        "apartmentName", "Jongno Map Test",
                        "dealAmountManwon", dealAmountManwon,
                        "exclusiveAreaM2", 84.97
                ))
        );
    }

    private static JsonNode findTarget(JsonNode targets, String targetId) {
        for (JsonNode target : targets) {
            if (targetId.equals(target.path("targetId").asText())) {
                return target;
            }
        }
        return null;
    }
}
