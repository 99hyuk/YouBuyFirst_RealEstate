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
import org.springframework.test.annotation.DirtiesContext;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_EACH_TEST_METHOD)
class RealEstateMapLayerIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

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
                .containsExactly("month", "quarter", "halfYear");
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
    void refreshPrefersOfficialRebPriceIndexForMonthlyMapLayer() throws Exception {
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
                                officialPriceIndexFact(
                                        "region-seoul-jongno",
                                        "11110",
                                        "reb_rone_regional_price_change:A_2024_00045:202605:11110",
                                        1.06
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
        assertThat(month.path("sampleCount").asInt()).isEqualTo(1);
        assertThat(month.path("confidence").asDouble()).isEqualTo(100.0);
        assertThat(month.path("asOf").asText()).isEqualTo("2026-05-01T00:00:00Z");
        assertThat(month.path("provider").asText()).isEqualTo("reb");
        assertThat(month.path("sourceLabel").asText()).contains("R-ONE");
        assertThat(month.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(month.path("stale").asBoolean()).isFalse();
    }

    @Test
    void refreshCompoundsOfficialRebPriceIndexForQuarterAndHalfYearMapLayer() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                officialPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "reb_rone_regional_price_change:A_2024_00045:202512:11110",
                                        "2025-12-01",
                                        1.0
                                ),
                                officialPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "reb_rone_regional_price_change:A_2024_00045:202601:11110",
                                        "2026-01-01",
                                        1.0
                                ),
                                officialPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "reb_rone_regional_price_change:A_2024_00045:202602:11110",
                                        "2026-02-01",
                                        1.0
                                ),
                                officialPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "reb_rone_regional_price_change:A_2024_00045:202603:11110",
                                        "2026-03-01",
                                        1.0
                                ),
                                officialPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "reb_rone_regional_price_change:A_2024_00045:202604:11110",
                                        "2026-04-01",
                                        1.0
                                ),
                                officialPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "reb_rone_regional_price_change:A_2024_00045:202605:11110",
                                        "2026-05-01",
                                        1.0
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
        assertThat(quarter.path("changePct").asDouble()).isEqualTo(3.0301);
        assertThat(quarter.path("sampleCount").asInt()).isEqualTo(3);
        assertThat(quarter.path("asOf").asText()).isEqualTo("2026-05-01T00:00:00Z");
        assertThat(quarter.path("provider").asText()).isEqualTo("reb");
        assertThat(quarter.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(quarter.path("stale").asBoolean()).isFalse();

        JsonNode halfYear = jongno.path("periods").path("halfYear");
        assertThat(halfYear.path("changePct").asDouble()).isEqualTo(6.152);
        assertThat(halfYear.path("sampleCount").asInt()).isEqualTo(6);
        assertThat(halfYear.path("provider").asText()).isEqualTo("reb");
        assertThat(halfYear.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(halfYear.path("stale").asBoolean()).isFalse();
    }

    @Test
    void refreshUsesMonthlyRonePriceIndexBackfillForAllMapPeriods() throws Exception {
        ResponseEntity<String> marketFacts = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                monthlyPriceIndexFactAt(null, "11110", "2025-12-01", 1.0),
                                monthlyPriceIndexFactAt(null, "11110", "2026-01-01", 1.0),
                                monthlyPriceIndexFactAt(null, "11110", "2026-02-01", 1.0),
                                monthlyPriceIndexFactAt(null, "11110", "2026-03-01", 1.0),
                                monthlyPriceIndexFactAt(null, "11110", "2026-04-01", 1.0),
                                monthlyPriceIndexFactAt(null, "11110", "2026-05-01", 1.0),
                                officialPriceIndexFactAt(
                                        "region-seoul-jongno",
                                        "11110",
                                        "reb_rone_regional_price_change:A_2024_00045:202605:11110",
                                        "2026-05-01",
                                        99.0
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> refresh = restTemplate.postForEntity(
                "/internal/realestate/map/layer-snapshots/refresh",
                Map.of(
                        "layerType", "sigungu",
                        "periods", List.of("month", "quarter", "halfYear"),
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
        assertThat(refresh.getBody()).contains("\"acceptedSnapshots\":3");
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode jongno = findTarget(objectMapper.readTree(response.getBody()).path("targets"), "region-seoul-jongno");
        assertThat(jongno).isNotNull();

        JsonNode month = jongno.path("periods").path("month");
        assertThat(month.path("changePct").asDouble()).isEqualTo(1.0);
        assertThat(month.path("provider").asText()).isEqualTo("reb");
        assertThat(month.path("sourceLabel").asText()).contains("R-ONE");

        JsonNode quarter = jongno.path("periods").path("quarter");
        assertThat(quarter.path("changePct").asDouble()).isEqualTo(3.0301);
        assertThat(quarter.path("sampleCount").asInt()).isEqualTo(3);

        JsonNode halfYear = jongno.path("periods").path("halfYear");
        assertThat(halfYear.path("changePct").asDouble()).isEqualTo(6.152);
        assertThat(halfYear.path("sampleCount").asInt()).isEqualTo(6);
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

    private static Map<String, Object> officialPriceIndexFact(
            String targetId,
            String legalDongCode,
            String providerObjectId,
            double changePct
    ) {
        return officialPriceIndexFactAt(targetId, legalDongCode, providerObjectId, "2026-05-01", changePct);
    }

    private static Map<String, Object> officialPriceIndexFactAt(
            String targetId,
            String legalDongCode,
            String providerObjectId,
            String observedAt,
            double changePct
    ) {
        return Map.ofEntries(
                Map.entry("targetType", "region"),
                Map.entry("targetId", targetId),
                Map.entry("factType", "sale_price_index_change_pct"),
                Map.entry("provider", "reb"),
                Map.entry("providerDataset", "reb_rone_regional_price_change"),
                Map.entry("providerObjectId", providerObjectId),
                Map.entry("legalDongCode", legalDongCode),
                Map.entry("observedAt", observedAt),
                Map.entry("asOf", observedAt),
                Map.entry("ingestedAt", "2026-06-12T00:00:00Z"),
                Map.entry("sourceUpdatedAt", "2026-06-12T00:00:00Z"),
                Map.entry("dataStatus", "ok"),
                Map.entry("stale", false),
                Map.entry("valueJson", Map.of(
                        "regionName", "???",
                        "metricName", "?????? ???",
                        "housingType", "???",
                        "surveyName", "??????????",
                        "value", changePct,
                        "unit", "%",
                        "sourceLabel", "REB R-ONE regional apartment sale price index change"
                ))
        );
    }

    private static Map<String, Object> monthlyPriceIndexFactAt(
            String targetId,
            String legalDongCode,
            String observedAt,
            double changePct
    ) {
        String periodKey = observedAt.substring(0, 7).replace("-", "");
        Map<String, Object> item = new LinkedHashMap<>();
        item.put("targetType", "region");
        if (targetId != null) {
            item.put("targetId", targetId);
        }
        item.put("factType", "sale_price_index_change_pct");
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
                "value", changePct,
                "unit", "%",
                "sourceLabel", "REB R-ONE monthly apartment sale price index"
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
