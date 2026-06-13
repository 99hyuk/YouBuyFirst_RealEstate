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
class RealEstateAliasIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void upsertsAliasesAndExposesOnlyApprovedNonAmbiguousAliasesForMatcher() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("alias", "종로 재건축"),
                                Map.entry("aliasType", "community_slang"),
                                Map.entry("source", "manual:seed"),
                                Map.entry("evidenceUrl", "https://example.com/jongno"),
                                Map.entry("confidence", 0.86),
                                Map.entry("reviewState", "approved"),
                                Map.entry("createdBy", "operator"),
                                Map.entry("ambiguous", false)
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("alias", "종로"),
                                Map.entry("aliasType", "short_name"),
                                Map.entry("source", "crawler:candidate"),
                                Map.entry("confidence", 0.52),
                                Map.entry("reviewState", "candidate"),
                                Map.entry("createdBy", "system"),
                                Map.entry("ambiguous", false)
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul"),
                                Map.entry("alias", "서울"),
                                Map.entry("aliasType", "official"),
                                Map.entry("source", "seed:region"),
                                Map.entry("confidence", 1.0),
                                Map.entry("reviewState", "approved"),
                                Map.entry("createdBy", "import"),
                                Map.entry("ambiguous", true)
                        )
                )
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/aliases/candidates",
                request,
                String.class
        );
        ResponseEntity<String> update = restTemplate.postForEntity(
                "/internal/realestate/aliases/candidates",
                Map.of(
                        "items",
                        List.of(Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("alias", " 종로-재건축 "),
                                Map.entry("aliasType", "community_slang"),
                                Map.entry("source", "manual:review"),
                                Map.entry("evidenceUrl", "https://example.com/jongno-updated"),
                                Map.entry("confidence", 0.91),
                                Map.entry("reviewState", "approved"),
                                Map.entry("createdBy", "operator"),
                                Map.entry("ambiguous", false)
                        ))
                ),
                String.class
        );
        ResponseEntity<String> publicAliases = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/aliases",
                String.class,
                "region-seoul-jongno"
        );
        ResponseEntity<String> matcherAliases = restTemplate.getForEntity(
                "/internal/realestate/aliases?reviewState=approved&ambiguous=false&targetType=region",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode ingestRoot = objectMapper.readTree(ingest.getBody());
        assertThat(ingestRoot.path("acceptedAliases").asInt()).isEqualTo(3);
        assertThat(ingestRoot.path("createdAliases").asInt()).isEqualTo(3);

        assertThat(update.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode updateRoot = objectMapper.readTree(update.getBody());
        assertThat(updateRoot.path("acceptedAliases").asInt()).isEqualTo(1);
        assertThat(updateRoot.path("updatedAliases").asInt()).isEqualTo(1);

        assertThat(publicAliases.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode publicItems = objectMapper.readTree(publicAliases.getBody()).path("items");
        assertThat(publicItems).hasSize(1);
        assertThat(publicItems.get(0).path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(publicItems.get(0).path("alias").asText()).isEqualTo("종로-재건축");
        assertThat(publicItems.get(0).path("normalizedAlias").asText()).isEqualTo("종로재건축");
        assertThat(publicItems.get(0).path("source").asText()).isEqualTo("manual:review");
        assertThat(publicItems.get(0).path("evidenceUrl").asText()).isEqualTo("https://example.com/jongno-updated");
        assertThat(publicItems.get(0).path("confidence").asDouble()).isEqualTo(0.91);
        assertThat(publicItems.get(0).path("reviewState").asText()).isEqualTo("approved");
        assertThat(publicItems.get(0).path("ambiguous").asBoolean()).isFalse();

        assertThat(matcherAliases.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode matcherItems = objectMapper.readTree(matcherAliases.getBody()).path("items");
        assertThat(matcherItems).hasSize(1);
        assertThat(matcherItems.get(0).path("alias").asText()).isEqualTo("종로-재건축");
        assertThat(matcherItems.get(0).path("aliasType").asText()).isEqualTo("community_slang");
        assertThat(matcherItems.get(0).path("targetType").asText()).isEqualTo("region");
        assertThat(matcherItems.get(0).path("targetId").asText()).isEqualTo("region-seoul-jongno");
    }
}
