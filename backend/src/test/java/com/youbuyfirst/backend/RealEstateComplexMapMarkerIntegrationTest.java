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
class RealEstateComplexMapMarkerIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void exposesComplexMarkersForARegionTarget() throws Exception {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/nearby-complexes?limit=10",
                String.class,
                "region-seoul-mapo"
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.path("targetId").asText()).isEqualTo("region-seoul-mapo");
        assertThat(body.path("dataStatus").asText()).isEqualTo("mock");
        assertThat(body.path("stale").asBoolean()).isTrue();
        assertThat(body.path("items")).hasSize(3);

        JsonNode marker = findMarker(body.path("items"), "complex-mapo-raemian-prugio");
        assertThat(marker).isNotNull();
        assertThat(marker.path("latitude").asDouble()).isEqualTo(37.5536);
        assertThat(marker.path("longitude").asDouble()).isEqualTo(126.9564);
        assertThat(marker.path("provider").asText()).isEqualTo("front_fixture");
        assertThat(marker.path("dataStatus").asText()).isEqualTo("mock");
        assertThat(marker.path("coordinateStatus").asText()).isEqualTo("mock");
    }

    @Test
    void exposesTheComplexItselfForAComplexTarget() throws Exception {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/nearby-complexes",
                String.class,
                "complex-mapo-raemian-prugio"
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.path("items")).hasSize(1);
        assertThat(body.path("items").get(0).path("targetId").asText()).isEqualTo("complex-mapo-raemian-prugio");
    }

    @Test
    void resolvesCommunityObservedComplexMarkersThroughCanonicalNameMatch() throws Exception {
        Map<String, Object> targetRequest = Map.of(
                "items",
                List.of(
                        Map.of(
                                "targetId", "complex-test-canonical-marker-match",
                                "targetType", "complex",
                                "displayName", "Canonical Palace Marker Match",
                                "slug", "canonical-palace-marker-match",
                                "reviewState", "approved",
                                "dataStatus", "ok"
                        ),
                        Map.of(
                                "targetId", "complex-community-test-marker-match",
                                "targetType", "complex",
                                "displayName", "Canonical Palace Marker Match",
                                "slug", "community-test-marker-match",
                                "reviewState", "candidate",
                                "dataStatus", "community_observed"
                        )
                )
        );
        Map<String, Object> complexRequest = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetId", "complex-test-canonical-marker-match"),
                                Map.entry("regionTargetId", "region-seoul-jongno"),
                                Map.entry("legalDongCode", "1111010100"),
                                Map.entry("jibunAddress", "canonical marker address"),
                                Map.entry("source", "ssafy_home:test"),
                                Map.entry("latitude", 37.5711),
                                Map.entry("longitude", 126.9822),
                                Map.entry("coordinateProvider", "ssafy_home:test"),
                                Map.entry("coordinateAsOf", "2026-06-16T00:00:00Z"),
                                Map.entry("coordinateStatus", "ok"),
                                Map.entry("markerDataStatus", "ok"),
                                Map.entry("markerStale", false)
                        ),
                        Map.ofEntries(
                                Map.entry("targetId", "complex-community-test-marker-match"),
                                Map.entry("regionTargetId", "region-seoul-jongno"),
                                Map.entry("legalDongCode", "1111010100"),
                                Map.entry("jibunAddress", "community observed address"),
                                Map.entry("source", "community:observed"),
                                Map.entry("coordinateStatus", "candidate"),
                                Map.entry("markerDataStatus", "community_observed"),
                                Map.entry("markerStale", true)
                        )
                )
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
        ResponseEntity<String> nearby = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/nearby-complexes?limit=5",
                String.class,
                "complex-community-test-marker-match"
        );

        assertThat(targetResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(complexResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(nearby.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode body = objectMapper.readTree(nearby.getBody());
        JsonNode canonicalMarker = findMarker(body.path("items"), "complex-test-canonical-marker-match");
        assertThat(canonicalMarker).isNotNull();
        assertThat(canonicalMarker.path("latitude").asDouble()).isEqualTo(37.5711);
        assertThat(canonicalMarker.path("longitude").asDouble()).isEqualTo(126.9822);
        assertThat(canonicalMarker.path("provider").asText()).isEqualTo("ssafy_home:test");
    }

    @Test
    void upsertsComplexRegistryRowsFromPublicMarketFactPipeline() throws Exception {
        Map<String, Object> targetRequest = Map.of(
                "items",
                List.of(Map.of(
                        "targetId", "complex-molit-11110-sajik-palace",
                        "targetType", "complex",
                        "displayName", "Sajik Palace",
                        "slug", "molit-11110-sajik-palace",
                        "reviewState", "approved",
                        "dataStatus", "partial"
                ))
        );
        Map<String, Object> complexRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetId", "complex-molit-11110-sajik-palace"),
                        Map.entry("regionTargetId", "region-seoul-jongno"),
                        Map.entry("legalDongCode", "11110"),
                        Map.entry("jibunAddress", "Sajik-dong 1-1"),
                        Map.entry("normalizedAddress", "11110Sajikdong11SajikPalace"),
                        Map.entry("builtYear", 2015),
                        Map.entry("source", "molit:market-fact"),
                        Map.entry("latitude", 37.5751),
                        Map.entry("longitude", 126.9687),
                        Map.entry("coordinateProvider", "kakao_local_search:keyword"),
                        Map.entry("coordinateAsOf", "2026-06-16T00:00:00Z"),
                        Map.entry("coordinateStatus", "candidate"),
                        Map.entry("markerTone", "flat"),
                        Map.entry("priceSummary", "확인 필요"),
                        Map.entry("changeLabel", "unknown"),
                        Map.entry("reactionSummary", "반응 지표 연결 전"),
                        Map.entry("markerNote", "테스트 좌표 후보"),
                        Map.entry("markerDataStatus", "partial"),
                        Map.entry("markerStale", true)
                ))
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
        ResponseEntity<String> nearby = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/nearby-complexes?limit=20",
                String.class,
                "region-seoul-jongno"
        );

        assertThat(targetResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(complexResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(complexResponse.getBody()).contains("\"acceptedComplexes\":1");

        JsonNode body = objectMapper.readTree(nearby.getBody());
        JsonNode marker = findMarker(body.path("items"), "complex-molit-11110-sajik-palace");
        assertThat(marker).isNotNull();
        assertThat(marker.path("name").asText()).isEqualTo("Sajik Palace");
        assertThat(marker.path("address").asText()).isEqualTo("Sajik-dong 1-1");
        assertThat(marker.path("provider").asText()).isEqualTo("kakao_local_search:keyword");
        assertThat(marker.path("latitude").asDouble()).isEqualTo(37.5751);
        assertThat(marker.path("longitude").asDouble()).isEqualTo(126.9687);
        assertThat(marker.path("coordinateStatus").asText()).isEqualTo("candidate");
        assertThat(marker.path("dataStatus").asText()).isEqualTo("partial");
        assertThat(marker.path("stale").asBoolean()).isTrue();
        assertThat(marker.path("legalDongCode").asText()).isEqualTo("11110");
    }

    @Test
    void returnsNotFoundForUnknownTargets() {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/nearby-complexes",
                String.class,
                "region-unknown"
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }

    private static JsonNode findMarker(JsonNode markers, String targetId) {
        for (JsonNode marker : markers) {
            if (targetId.equals(marker.path("targetId").asText())) {
                return marker;
            }
        }
        return null;
    }
}
