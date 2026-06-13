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
        assertThat(body.path("asOf").asText()).startsWith("2026-06-01");
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

    private static JsonNode findTarget(JsonNode targets, String targetId) {
        for (JsonNode target : targets) {
            if (targetId.equals(target.path("targetId").asText())) {
                return target;
            }
        }
        return null;
    }
}
