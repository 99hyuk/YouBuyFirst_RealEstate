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
class RealEstateTargetIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void searchesSeededRegionsAndExposesPublicDataCollectionTargets() throws Exception {
        ResponseEntity<String> search = restTemplate.getForEntity(
                "/api/realestate/targets/search?q={query}",
                String.class,
                "종로"
        );
        ResponseEntity<String> dataTargets = restTemplate.getForEntity(
                "/internal/realestate/market-data-targets?enabled=true",
                String.class
        );

        assertThat(search.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode targetItems = objectMapper.readTree(search.getBody()).path("items");
        assertThat(targetItems).hasSize(1);
        assertThat(targetItems.get(0).path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(targetItems.get(0).path("displayName").asText()).isEqualTo("서울 종로구");
        assertThat(targetItems.get(0).path("targetType").asText()).isEqualTo("region");
        assertThat(targetItems.get(0).path("regionLevel").asText()).isEqualTo("sigungu");
        assertThat(targetItems.get(0).path("parentTargetId").asText()).isEqualTo("region-seoul");
        assertThat(targetItems.get(0).path("legalDongCode").asText()).isEqualTo("11110");

        assertThat(dataTargets.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode dataTargetItems = objectMapper.readTree(dataTargets.getBody()).path("items");
        assertThat(dataTargetItems)
                .extracting(item -> item.path("providerDataset").asText())
                .contains("molit_apt_trade", "molit_apt_rent");
        JsonNode jongnoTarget = null;
        for (JsonNode item : dataTargetItems) {
            if ("region-seoul-jongno".equals(item.path("targetId").asText())
                    && "molit_apt_trade".equals(item.path("providerDataset").asText())) {
                jongnoTarget = item;
                break;
            }
        }
        assertThat(jongnoTarget).isNotNull();
        assertThat(jongnoTarget.path("lawdCode").asText()).isEqualTo("11110");
        assertThat(jongnoTarget.path("refreshIntervalHours").asInt()).isEqualTo(24);
        assertThat(jongnoTarget.path("staleAfterHours").asInt()).isEqualTo(72);
    }

    @Test
    void mapsMarketFactToSeededRegionWhenTargetIdIsMissing() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetType", "region"),
                        Map.entry("factType", "apt_rent"),
                        Map.entry("provider", "molit"),
                        Map.entry("providerDataset", "molit_apt_rent"),
                        Map.entry("providerObjectId", "molit_apt_rent:11110:202606:auto-target"),
                        Map.entry("legalDongCode", "11110"),
                        Map.entry("observedAt", "2026-06-05"),
                        Map.entry("asOf", "2026-06-01"),
                        Map.entry("ingestedAt", "2026-06-11T00:15:00Z"),
                        Map.entry("dataStatus", "ok"),
                        Map.entry("stale", false),
                        Map.entry("valueJson", Map.of(
                                "apartmentName", "Sajik Palace",
                                "depositAmountManwon", 45000,
                                "monthlyRentAmountManwon", 120
                        ))
                ))
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                request,
                String.class
        );
        ResponseEntity<String> list = restTemplate.getForEntity(
                "/api/realestate/market-facts?legalDongCode=11110&factType=apt_rent",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode fact = objectMapper.readTree(list.getBody()).path("items").get(0);
        assertThat(fact.path("targetType").asText()).isEqualTo("region");
        assertThat(fact.path("targetId").asText()).isEqualTo("region-seoul-jongno");
    }

    @Test
    void importsRegionsAndCreatesMolitMarketDataTargetsForSigungu() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetId", "region-busan"),
                                Map.entry("displayName", "부산광역시"),
                                Map.entry("slug", "busan"),
                                Map.entry("regionLevel", "sido"),
                                Map.entry("legalDongCode", "26000"),
                                Map.entry("regionCode", "26"),
                                Map.entry("source", "import:molit-legal-dong-code")
                        ),
                        Map.ofEntries(
                                Map.entry("targetId", "region-busan-haeundae"),
                                Map.entry("displayName", "부산 해운대구"),
                                Map.entry("slug", "busan-haeundae"),
                                Map.entry("regionLevel", "sigungu"),
                                Map.entry("parentTargetId", "region-busan"),
                                Map.entry("legalDongCode", "26350"),
                                Map.entry("regionCode", "26350"),
                                Map.entry("source", "import:molit-legal-dong-code")
                        )
                )
        );

        ResponseEntity<String> importResponse = restTemplate.postForEntity(
                "/internal/realestate/regions",
                request,
                String.class
        );
        ResponseEntity<String> search = restTemplate.getForEntity(
                "/api/realestate/targets/search?q={query}",
                String.class,
                "해운대"
        );
        ResponseEntity<String> dataTargets = restTemplate.getForEntity(
                "/internal/realestate/market-data-targets?enabled=true&limit=20",
                String.class
        );

        assertThat(importResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(importResponse.getBody()).contains("\"acceptedRegions\":2");

        JsonNode targetItems = objectMapper.readTree(search.getBody()).path("items");
        assertThat(targetItems).hasSize(1);
        assertThat(targetItems.get(0).path("targetId").asText()).isEqualTo("region-busan-haeundae");
        assertThat(targetItems.get(0).path("parentTargetId").asText()).isEqualTo("region-busan");
        assertThat(targetItems.get(0).path("legalDongCode").asText()).isEqualTo("26350");

        JsonNode marketTargetItems = objectMapper.readTree(dataTargets.getBody()).path("items");
        assertThat(marketTargetItems)
                .filteredOn(item -> "region-busan-haeundae".equals(item.path("targetId").asText()))
                .extracting(item -> item.path("providerDataset").asText())
                .containsExactlyInAnyOrder("molit_apt_trade", "molit_apt_rent");
    }
}
