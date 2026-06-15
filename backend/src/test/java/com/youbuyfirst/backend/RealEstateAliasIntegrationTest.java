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
    void exposesSeededRegionAliasesForMatcher() throws Exception {
        ResponseEntity<String> matcherAliases = restTemplate.getForEntity(
                "/internal/realestate/aliases?reviewState=approved&ambiguous=false&targetType=region&limit=200",
                String.class
        );

        assertThat(matcherAliases.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(matcherAliases.getBody()).path("items");
        assertThat(items).anySatisfy(item -> {
            assertThat(item.path("targetId").asText()).isEqualTo("region-seoul");
            assertThat(item.path("alias").asText()).isEqualTo("서울");
        });
        assertThat(items).anySatisfy(item -> {
            assertThat(item.path("targetId").asText()).isEqualTo("region-gyeonggi");
            assertThat(item.path("alias").asText()).isEqualTo("경기");
        });
        assertThat(items).anySatisfy(item -> {
            assertThat(item.path("targetId").asText()).isEqualTo("region-daejeon");
            assertThat(item.path("alias").asText()).isEqualTo("대전");
        });
        assertThat(items).anySatisfy(item -> {
            assertThat(item.path("targetId").asText()).isEqualTo("region-seoul-mapo");
            assertThat(item.path("alias").asText()).isEqualTo("마포구");
        });
    }

    @Test
    void upsertsAliasesAndExposesOnlyApprovedNonAmbiguousAliasesForMatcher() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("alias", "jongno-rebuild"),
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
                                Map.entry("alias", "jongno"),
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
                                Map.entry("alias", "seoul-hot"),
                                Map.entry("aliasType", "community_slang"),
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
                                Map.entry("alias", " jongno rebuild "),
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
        assertThat(publicItems).anySatisfy(item -> {
            assertThat(item.path("targetId").asText()).isEqualTo("region-seoul-jongno");
            assertThat(item.path("alias").asText()).isEqualTo("jongno rebuild");
            assertThat(item.path("normalizedAlias").asText()).isEqualTo("jongnorebuild");
            assertThat(item.path("aliasType").asText()).isEqualTo("community_slang");
            assertThat(item.path("source").asText()).isEqualTo("manual:review");
            assertThat(item.path("evidenceUrl").asText()).isEqualTo("https://example.com/jongno-updated");
            assertThat(item.path("confidence").asDouble()).isEqualTo(0.91);
            assertThat(item.path("reviewState").asText()).isEqualTo("approved");
            assertThat(item.path("ambiguous").asBoolean()).isFalse();
        });

        assertThat(matcherAliases.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode matcherItems = objectMapper.readTree(matcherAliases.getBody()).path("items");
        assertThat(matcherItems).anySatisfy(item -> {
            assertThat(item.path("alias").asText()).isEqualTo("jongno rebuild");
            assertThat(item.path("aliasType").asText()).isEqualTo("community_slang");
            assertThat(item.path("targetType").asText()).isEqualTo("region");
            assertThat(item.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        });
    }
}
