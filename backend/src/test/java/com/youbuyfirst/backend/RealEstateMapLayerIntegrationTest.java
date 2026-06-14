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
class RealEstateMapLayerIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void exposesNationwideSidoMapLayerSnapshots() throws Exception {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sido",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.path("layerType").asText()).isEqualTo("sido");
        assertThat(body.path("dataStatus").asText()).isEqualTo("mock");
        assertThat(body.path("stale").asBoolean()).isTrue();
        assertThat(body.path("asOf").asText()).isNotBlank();
        assertThat(body.path("periods"))
                .extracting(JsonNode::asText)
                .containsExactly("week", "month", "halfYear");
        assertThat(body.path("targets")).hasSize(17);

        JsonNode seoul = findTarget(body.path("targets"), "region-seoul");
        assertThat(seoul).isNotNull();
        assertThat(seoul.path("regionCode").asText()).isEqualTo("11");
        assertThat(seoul.path("geometryId").asText()).isEqualTo("sido-11");
        assertThat(seoul.path("periods").path("month").path("changePct").asDouble()).isEqualTo(0.62);
        assertThat(seoul.path("periods").path("month").path("confidence").asDouble()).isEqualTo(82.0);
        assertThat(seoul.path("periods").path("month").path("provider").asText()).isEqualTo("seed");
    }

    @Test
    void exposesAvailableSigunguLayerForAParentRegion() throws Exception {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.path("layerType").asText()).isEqualTo("sigungu");
        assertThat(body.path("parentTargetId").asText()).isEqualTo("region-seoul");
        assertThat(body.path("parentRegionCode").asText()).isEqualTo("11");
        assertThat(body.path("targets")).hasSize(2);

        JsonNode mapo = findTarget(body.path("targets"), "region-seoul-mapo");
        assertThat(mapo).isNotNull();
        assertThat(mapo.path("regionCode").asText()).isEqualTo("11140");
        assertThat(mapo.path("legalDongCode").asText()).isEqualTo("11440");
        assertThat(mapo.path("periods").path("month").path("changePct").asDouble()).isEqualTo(0.31);
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
                        "asOf", "2026-06-12T00:00:00Z"
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
        assertThat(month.path("asOf").asText()).isEqualTo("2026-06-12T00:00:00Z");
        assertThat(month.path("provider").asText()).isEqualTo("real_estate_map_layer_refresh");
        assertThat(month.path("sourceLabel").asText()).contains("실거래", "반응 snapshot");
        assertThat(month.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(month.path("stale").asBoolean()).isFalse();
    }

    private static Map<String, Object> mapFact(String providerObjectId, String observedAt, int dealAmountManwon) {
        return Map.ofEntries(
                Map.entry("targetType", "region"),
                Map.entry("targetId", "region-seoul-jongno"),
                Map.entry("factType", "apt_trade"),
                Map.entry("provider", "molit"),
                Map.entry("providerDataset", "molit_apt_trade"),
                Map.entry("providerObjectId", providerObjectId),
                Map.entry("legalDongCode", "11110"),
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
