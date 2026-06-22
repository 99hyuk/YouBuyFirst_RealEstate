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
class RealEstateTargetGraphIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void upsertsTargetEdgesAndExposesApprovedGraphForRollupAndDrilldown() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("fromTargetType", "region"),
                                Map.entry("fromTargetId", "region-seoul"),
                                Map.entry("toTargetType", "region"),
                                Map.entry("toTargetId", "region-seoul-jongno"),
                                Map.entry("edgeType", "contains"),
                                Map.entry("confidence", 1.0),
                                Map.entry("source", "seed:legal-dong"),
                                Map.entry("reviewState", "approved")
                        ),
                        Map.ofEntries(
                                Map.entry("fromTargetType", "region"),
                                Map.entry("fromTargetId", "region-seoul-jongno"),
                                Map.entry("toTargetType", "region"),
                                Map.entry("toTargetId", "region-seoul"),
                                Map.entry("edgeType", "nearby"),
                                Map.entry("confidence", 0.42),
                                Map.entry("source", "crawler:candidate"),
                                Map.entry("reviewState", "candidate")
                        )
                )
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/target-edges",
                request,
                String.class
        );
        ResponseEntity<String> update = restTemplate.postForEntity(
                "/internal/realestate/target-edges",
                Map.of(
                        "items",
                        List.of(Map.ofEntries(
                                Map.entry("fromTargetType", "region"),
                                Map.entry("fromTargetId", "region-seoul"),
                                Map.entry("toTargetType", "region"),
                                Map.entry("toTargetId", "region-seoul-jongno"),
                                Map.entry("edgeType", "contains"),
                                Map.entry("confidence", 0.98),
                                Map.entry("source", "manual:review"),
                                Map.entry("reviewState", "approved")
                        ))
                ),
                String.class
        );
        ResponseEntity<String> publicGraph = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/graph?direction=out",
                String.class,
                "region-seoul"
        );
        ResponseEntity<String> childGraph = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/graph?direction=in",
                String.class,
                "region-seoul-jongno"
        );
        ResponseEntity<String> internalEdges = restTemplate.getForEntity(
                "/internal/realestate/target-edges?reviewState=approved&edgeType=contains",
                String.class
        );
        ResponseEntity<String> snapshotIngest = restTemplate.postForEntity(
                "/internal/realestate/reaction-snapshots",
                Map.of(
                        "items",
                        List.of(Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("windowStart", "2026-06-12T00:00:00Z"),
                                Map.entry("windowEnd", "2026-06-12T01:00:00Z"),
                                Map.entry("asOf", "2026-06-12T01:03:00Z"),
                                Map.entry("mentionCount", 34),
                                Map.entry("previousMentionCount", 17),
                                Map.entry("expectationScore", 50),
                                Map.entry("concernScore", 35),
                                Map.entry("neutralScore", 15),
                                Map.entry("heatScore", 71),
                                Map.entry("confidence", 0.72),
                                Map.entry("sourceCount", 3),
                                Map.entry("sourceSkew", 0.44),
                                Map.entry("coverageStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("issues", List.of(Map.of(
                                        "issueKey", "redevelopment",
                                        "label", "재건축",
                                        "share", 0.38,
                                        "direction", "expectation",
                                        "summary", "재건축 기대가 하위 지역에서 반복됩니다.",
                                        "confidence", 0.77
                                )))
                        ))
                ),
                String.class
        );
        ResponseEntity<String> reactionGraph = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/reaction-graph?direction=out&edgeType=contains&windowStart=2026-06-12T00:00:00Z&windowMinutes=60",
                String.class,
                "region-seoul"
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode ingestRoot = objectMapper.readTree(ingest.getBody());
        assertThat(ingestRoot.path("acceptedEdges").asInt()).isEqualTo(2);
        assertThat(ingestRoot.path("createdEdges").asInt()).isEqualTo(2);

        assertThat(update.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode updateRoot = objectMapper.readTree(update.getBody());
        assertThat(updateRoot.path("acceptedEdges").asInt()).isEqualTo(1);
        assertThat(updateRoot.path("updatedEdges").asInt()).isEqualTo(1);

        assertThat(publicGraph.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode publicRoot = objectMapper.readTree(publicGraph.getBody());
        assertThat(publicRoot.path("targetId").asText()).isEqualTo("region-seoul");
        assertThat(publicRoot.path("direction").asText()).isEqualTo("out");
        JsonNode publicItems = publicRoot.path("items");
        assertThat(publicItems).hasSize(1);
        assertThat(publicItems.get(0).path("fromTargetId").asText()).isEqualTo("region-seoul");
        assertThat(publicItems.get(0).path("fromDisplayName").asText()).isEqualTo("서울특별시");
        assertThat(publicItems.get(0).path("toTargetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(publicItems.get(0).path("toDisplayName").asText()).isEqualTo("서울 종로구");
        assertThat(publicItems.get(0).path("edgeType").asText()).isEqualTo("contains");
        assertThat(publicItems.get(0).path("confidence").asDouble()).isEqualTo(0.98);
        assertThat(publicItems.get(0).path("source").asText()).isEqualTo("manual:review");
        assertThat(publicItems.get(0).path("reviewState").asText()).isEqualTo("approved");

        assertThat(childGraph.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode childItems = objectMapper.readTree(childGraph.getBody()).path("items");
        assertThat(childItems).hasSize(1);
        assertThat(childItems.get(0).path("fromTargetId").asText()).isEqualTo("region-seoul");

        assertThat(internalEdges.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode internalItems = objectMapper.readTree(internalEdges.getBody()).path("items");
        assertThat(internalItems).hasSize(1);
        assertThat(internalItems.get(0).path("toTargetId").asText()).isEqualTo("region-seoul-jongno");

        assertThat(snapshotIngest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(reactionGraph.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode reactionRoot = objectMapper.readTree(reactionGraph.getBody());
        assertThat(reactionRoot.path("targetId").asText()).isEqualTo("region-seoul");
        assertThat(reactionRoot.path("direction").asText()).isEqualTo("out");
        assertThat(reactionRoot.path("edgeType").asText()).isEqualTo("contains");
        assertThat(reactionRoot.path("windowStart").asText()).isEqualTo("2026-06-12T00:00:00Z");
        assertThat(reactionRoot.path("windowEnd").asText()).isEqualTo("2026-06-12T01:00:00Z");
        JsonNode reactionItems = reactionRoot.path("items");
        assertThat(reactionItems).hasSize(1);
        assertThat(reactionItems.get(0).path("edge").path("toTargetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(reactionItems.get(0).path("relatedTarget").path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(reactionItems.get(0).path("relatedTarget").path("displayName").asText()).isEqualTo("서울 종로구");
        assertThat(reactionItems.get(0).path("reactionSnapshot").path("mentionCount").asInt()).isEqualTo(34);
        assertThat(reactionItems.get(0).path("reactionSnapshot").path("dominantDirection").asText()).isEqualTo("expectation");
        assertThat(reactionItems.get(0).path("reactionSnapshot").path("issueMix").get(0).path("issueKey").asText()).isEqualTo("redevelopment");
    }

    @Test
    void pagesInternalTargetEdgesForLargeRollupExports() throws Exception {
        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/target-edges",
                Map.of(
                        "items",
                        List.of(
                                Map.ofEntries(
                                        Map.entry("fromTargetType", "region"),
                                        Map.entry("fromTargetId", "region-seoul"),
                                        Map.entry("toTargetType", "region"),
                                        Map.entry("toTargetId", "region-seoul-jongno"),
                                        Map.entry("edgeType", "contains"),
                                        Map.entry("confidence", 0.98),
                                        Map.entry("source", "test:pagination"),
                                        Map.entry("reviewState", "approved")
                                ),
                                Map.ofEntries(
                                        Map.entry("fromTargetType", "region"),
                                        Map.entry("fromTargetId", "region-seoul"),
                                        Map.entry("toTargetType", "region"),
                                        Map.entry("toTargetId", "region-seoul-mapo"),
                                        Map.entry("edgeType", "contains"),
                                        Map.entry("confidence", 0.97),
                                        Map.entry("source", "test:pagination"),
                                        Map.entry("reviewState", "approved")
                                )
                        )
                ),
                String.class
        );
        ResponseEntity<String> firstPage = restTemplate.getForEntity(
                "/internal/realestate/target-edges?targetId=region-seoul&direction=out&reviewState=approved&edgeType=contains&limit=1&page=0",
                String.class
        );
        ResponseEntity<String> secondPage = restTemplate.getForEntity(
                "/internal/realestate/target-edges?targetId=region-seoul&direction=out&reviewState=approved&edgeType=contains&limit=1&page=1",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(firstPage.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(secondPage.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode firstItem = objectMapper.readTree(firstPage.getBody()).path("items").path(0);
        JsonNode secondItem = objectMapper.readTree(secondPage.getBody()).path("items").path(0);
        assertThat(firstItem.path("fromTargetId").asText() + ">" + firstItem.path("toTargetId").asText())
                .isNotEqualTo(secondItem.path("fromTargetId").asText() + ">" + secondItem.path("toTargetId").asText());
    }

    @Test
    void importsGenericTargetsSoGraphCanRepresentLivingAreasAndPolicyAreas() throws Exception {
        ResponseEntity<String> targetImport = restTemplate.postForEntity(
                "/internal/realestate/targets",
                Map.of(
                        "items",
                        List.of(Map.ofEntries(
                                Map.entry("targetId", "living-area-seoul-core"),
                                Map.entry("targetType", "living_area"),
                                Map.entry("displayName", "서울 핵심 생활권"),
                                Map.entry("slug", "seoul-core-living-area"),
                                Map.entry("reviewState", "approved"),
                                Map.entry("dataStatus", "ok")
                        ))
                ),
                String.class
        );
        ResponseEntity<String> edgeImport = restTemplate.postForEntity(
                "/internal/realestate/target-edges",
                Map.of(
                        "items",
                        List.of(Map.ofEntries(
                                Map.entry("fromTargetType", "region"),
                                Map.entry("fromTargetId", "region-seoul"),
                                Map.entry("toTargetType", "living_area"),
                                Map.entry("toTargetId", "living-area-seoul-core"),
                                Map.entry("edgeType", "contains"),
                                Map.entry("confidence", 0.88),
                                Map.entry("source", "manual:living-area"),
                                Map.entry("reviewState", "approved")
                        ))
                ),
                String.class
        );
        ResponseEntity<String> graph = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/graph?direction=out&edgeType=contains",
                String.class,
                "region-seoul"
        );

        assertThat(targetImport.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode targetImportRoot = objectMapper.readTree(targetImport.getBody());
        assertThat(targetImportRoot.path("acceptedTargets").asInt()).isEqualTo(1);
        assertThat(targetImportRoot.path("createdTargets").asInt()).isEqualTo(1);

        assertThat(edgeImport.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode graphItems = objectMapper.readTree(graph.getBody()).path("items");
        assertThat(graphItems)
                .filteredOn(item -> "living-area-seoul-core".equals(item.path("toTargetId").asText()))
                .hasSize(1)
                .first()
                .satisfies(item -> {
                    assertThat(item.path("toTargetType").asText()).isEqualTo("living_area");
                    assertThat(item.path("toDisplayName").asText()).isEqualTo("서울 핵심 생활권");
                    assertThat(item.path("confidence").asDouble()).isEqualTo(0.88);
                });
    }

    @Test
    void reactionGraphReturnsNotFoundForUnknownTarget() {
        ResponseEntity<String> reactionGraph = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/reaction-graph?direction=out&edgeType=contains",
                String.class,
                "region-unknown"
        );

        assertThat(reactionGraph.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
    }
}
