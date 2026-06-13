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
