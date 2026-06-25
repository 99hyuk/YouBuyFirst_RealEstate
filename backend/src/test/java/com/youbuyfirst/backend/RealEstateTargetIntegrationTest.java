package com.youbuyfirst.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.realestate.RealEstateTargetRepository;
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

    private static final List<String> MOLIT_MARKET_DATASETS = List.of(
            "molit_apt_trade",
            "molit_apt_rent",
            "molit_offi_trade",
            "molit_offi_rent",
            "molit_rh_trade",
            "molit_rh_rent",
            "molit_sh_trade",
            "molit_sh_rent",
            "molit_silv_trade"
    );

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private RealEstateTargetRepository targetRepository;

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
                .containsAll(MOLIT_MARKET_DATASETS);
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
    void pagesMarketDataTargetsForLargeRegionExports() throws Exception {
        ResponseEntity<String> firstPage = restTemplate.getForEntity(
                "/internal/realestate/market-data-targets?enabled=true&limit=1&page=0",
                String.class
        );
        ResponseEntity<String> secondPage = restTemplate.getForEntity(
                "/internal/realestate/market-data-targets?enabled=true&limit=1&page=1",
                String.class
        );

        assertThat(firstPage.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(secondPage.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode firstItem = objectMapper.readTree(firstPage.getBody()).path("items").path(0);
        JsonNode secondItem = objectMapper.readTree(secondPage.getBody()).path("items").path(0);
        assertThat(firstItem.path("targetId").asText() + ":" + firstItem.path("providerDataset").asText())
                .isNotEqualTo(secondItem.path("targetId").asText() + ":" + secondItem.path("providerDataset").asText());
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
    void seedsCanonicalFrontendRouteTargetsInTheTargetRegistry() throws Exception {
        assertThat(targetRepository.findById("region-seoul-mapo"))
                .hasValueSatisfying(target -> {
                    assertThat(target.getTargetType()).isEqualTo("region");
                    assertThat(target.getSlug()).isEqualTo("seoul-mapo");
                    assertThat(target.getDataStatus()).isEqualTo("ok");
                });
        assertThat(targetRepository.findById("living-area-gyeonggi-dongtan-station"))
                .hasValueSatisfying(target -> {
                    assertThat(target.getTargetType()).isEqualTo("living_area");
                    assertThat(target.getDataStatus()).isEqualTo("mock");
                });
        assertThat(targetRepository.findById("complex-mapo-raemian-prugio"))
                .hasValueSatisfying(target -> {
                    assertThat(target.getTargetType()).isEqualTo("complex");
                    assertThat(target.getReviewState()).isEqualTo("candidate");
                });

        ResponseEntity<String> search = restTemplate.getForEntity(
                "/api/realestate/targets/search?q={query}",
                String.class,
                "마포"
        );
        ResponseEntity<String> dataTargets = restTemplate.getForEntity(
                "/internal/realestate/market-data-targets?enabled=true&limit=500",
                String.class
        );

        assertThat(search.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode targetItems = objectMapper.readTree(search.getBody()).path("items");
        assertThat(targetItems)
                .extracting(item -> item.path("targetId").asText())
                .contains("region-seoul-mapo");

        assertThat(dataTargets.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode dataTargetItems = objectMapper.readTree(dataTargets.getBody()).path("items");
        assertThat(dataTargetItems)
                .filteredOn(item -> "region-seoul-mapo".equals(item.path("targetId").asText()))
                .extracting(item -> item.path("providerDataset").asText())
                .containsExactlyInAnyOrderElementsOf(MOLIT_MARKET_DATASETS);
    }

    @Test
    void searchesComplexTargetsAlongsideRegionTargets() throws Exception {
        Map<String, Object> targetRequest = Map.of(
                "items",
                List.of(Map.of(
                        "targetId", "complex-test-raemian-palace-search",
                        "targetType", "complex",
                        "displayName", "Raemian Palace Search",
                        "slug", "raemian-palace-search",
                        "reviewState", "approved",
                        "dataStatus", "ok"
                ))
        );
        Map<String, Object> complexRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetId", "complex-test-raemian-palace-search"),
                        Map.entry("regionTargetId", "region-seoul-jongno"),
                        Map.entry("legalDongCode", "1144010100"),
                        Map.entry("jibunAddress", "test address"),
                        Map.entry("source", "test:search"),
                        Map.entry("markerDataStatus", "ok"),
                        Map.entry("markerStale", false)
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
        ResponseEntity<String> search = restTemplate.getForEntity(
                "/api/realestate/targets/search?q=raemian&limit=5",
                String.class
        );

        assertThat(targetResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(complexResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(search.getBody()).path("items");
        assertThat(items)
                .filteredOn(item -> "complex-test-raemian-palace-search".equals(item.path("targetId").asText()))
                .singleElement()
                .satisfies(item -> {
                    assertThat(item.path("targetType").asText()).isEqualTo("complex");
                    assertThat(item.path("regionLevel").asText()).isEqualTo("complex");
                    assertThat(item.path("parentTargetId").asText()).isEqualTo("region-seoul-jongno");
                    assertThat(item.path("legalDongCode").asText()).isEqualTo("1144010100");
                });
    }

    @Test
    void searchesTargetsByApprovedAliases() throws Exception {
        Map<String, Object> targetRequest = Map.of(
                "items",
                List.of(Map.of(
                        "targetId", "complex-test-mapo-alias-search",
                        "targetType", "complex",
                        "displayName", "Mapo Raemian Prugio Alias Search",
                        "slug", "mapo-raemian-prugio-alias-search",
                        "reviewState", "approved",
                        "dataStatus", "ok"
                ))
        );
        Map<String, Object> complexRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetId", "complex-test-mapo-alias-search"),
                        Map.entry("regionTargetId", "region-seoul-jongno"),
                        Map.entry("jibunAddress", "alias search address"),
                        Map.entry("source", "test:alias-search"),
                        Map.entry("markerDataStatus", "ok"),
                        Map.entry("markerStale", false)
                ))
        );
        Map<String, Object> aliasRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetType", "complex"),
                        Map.entry("targetId", "complex-test-mapo-alias-search"),
                        Map.entry("alias", "mapo shortcut"),
                        Map.entry("aliasType", "community_slang"),
                        Map.entry("source", "test:alias-search"),
                        Map.entry("confidence", 0.94),
                        Map.entry("reviewState", "approved"),
                        Map.entry("createdBy", "test"),
                        Map.entry("ambiguous", false)
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
        ResponseEntity<String> aliasResponse = restTemplate.postForEntity(
                "/internal/realestate/aliases",
                aliasRequest,
                String.class
        );
        ResponseEntity<String> search = restTemplate.getForEntity(
                "/api/realestate/targets/search?q={query}&limit=5",
                String.class,
                "mapo shortcut"
        );

        assertThat(targetResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(complexResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(aliasResponse.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode items = objectMapper.readTree(search.getBody()).path("items");
        assertThat(items)
                .filteredOn(item -> "complex-test-mapo-alias-search".equals(item.path("targetId").asText()))
                .singleElement()
                .satisfies(item -> {
                    assertThat(item.path("targetType").asText()).isEqualTo("complex");
                    assertThat(item.path("parentTargetId").asText()).isEqualTo("region-seoul-jongno");
                    assertThat(item.path("legalDongCode").asText()).isEqualTo("11110");
                    assertThat(item.path("regionCode").asText()).isEqualTo("11010");
                });
    }

    @Test
    void autocompleteSearchRequiresTwoCharactersAndCapsLargeLimits() throws Exception {
        Map<String, Object> targetRequest = Map.of(
                "items",
                java.util.stream.IntStream.range(0, 12)
                        .mapToObj(index -> Map.of(
                                "targetId", "complex-test-autocomplete-" + index,
                                "targetType", "complex",
                                "displayName", "검색테스트단지 " + index,
                                "slug", "autocomplete-test-" + index,
                                "reviewState", "approved",
                                "dataStatus", "ok"
                        ))
                        .toList()
        );

        ResponseEntity<String> targetResponse = restTemplate.postForEntity(
                "/internal/realestate/targets",
                targetRequest,
                String.class
        );
        ResponseEntity<String> tooShort = restTemplate.getForEntity(
                "/api/realestate/targets/search?q={query}&mode=autocomplete&limit=8",
                String.class,
                "검"
        );
        ResponseEntity<String> capped = restTemplate.getForEntity(
                "/api/realestate/targets/search?q={query}&mode=autocomplete&limit=500",
                String.class,
                "검색테스트"
        );

        assertThat(targetResponse.getStatusCode()).isEqualTo(HttpStatus.OK);

        assertThat(tooShort.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(objectMapper.readTree(tooShort.getBody()).path("items")).isEmpty();

        assertThat(capped.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode cappedItems = objectMapper.readTree(capped.getBody()).path("items");
        assertThat(cappedItems).hasSize(8);
        assertThat(cappedItems)
                .extracting(item -> item.path("targetType").asText())
                .containsOnly("complex");
    }

    @Test
    void autocompleteSearchFindsDongRegionsFromParentRegionAndDongTokens() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetId", "region-test-daejeon-token"),
                                Map.entry("displayName", "Daejeon"),
                                Map.entry("slug", "test-daejeon-token"),
                                Map.entry("regionLevel", "sido"),
                                Map.entry("legalDongCode", "30000"),
                                Map.entry("regionCode", "30"),
                                Map.entry("source", "test:token-search")
                        ),
                        Map.ofEntries(
                                Map.entry("targetId", "region-test-daejeon-seogu-token"),
                                Map.entry("displayName", "Daejeon Seo-gu"),
                                Map.entry("slug", "test-daejeon-seogu-token"),
                                Map.entry("regionLevel", "sigungu"),
                                Map.entry("parentTargetId", "region-test-daejeon-token"),
                                Map.entry("legalDongCode", "30170"),
                                Map.entry("regionCode", "30170"),
                                Map.entry("source", "test:token-search")
                        ),
                        Map.ofEntries(
                                Map.entry("targetId", "region-test-daejeon-seogu-galma-token"),
                                Map.entry("displayName", "Daejeon Seo-gu Galma-dong"),
                                Map.entry("slug", "test-daejeon-seogu-galma-token"),
                                Map.entry("regionLevel", "eupmyeondong"),
                                Map.entry("parentTargetId", "region-test-daejeon-seogu-token"),
                                Map.entry("legalDongCode", "3017011100"),
                                Map.entry("regionCode", "3017011100"),
                                Map.entry("source", "test:token-search")
                        )
                )
        );

        ResponseEntity<String> importResponse = restTemplate.postForEntity(
                "/internal/realestate/regions",
                request,
                String.class
        );
        ResponseEntity<String> search = restTemplate.getForEntity(
                "/api/realestate/targets/search?q={query}&mode=autocomplete&limit=8",
                String.class,
                "Daejeon Galma-dong"
        );

        assertThat(importResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(search.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode items = objectMapper.readTree(search.getBody()).path("items");
        assertThat(items)
                .filteredOn(item -> "region-test-daejeon-seogu-galma-token".equals(item.path("targetId").asText()))
                .singleElement()
                .satisfies(item -> {
                    assertThat(item.path("targetType").asText()).isEqualTo("region");
                    assertThat(item.path("regionLevel").asText()).isEqualTo("eupmyeondong");
                    assertThat(item.path("parentTargetId").asText()).isEqualTo("region-test-daejeon-seogu-token");
                    assertThat(item.path("legalDongCode").asText()).isEqualTo("3017011100");
                });
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
                "/internal/realestate/market-data-targets?enabled=true&limit=500",
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
                .containsExactlyInAnyOrderElementsOf(MOLIT_MARKET_DATASETS);
    }

    @Test
    void listsImportedEupmyeondongRegionsForComplexRegistryMapping() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetId", "region-test-mapo"),
                                Map.entry("displayName", "서울특별시 마포구"),
                                Map.entry("slug", "test-mapo"),
                                Map.entry("regionLevel", "sigungu"),
                                Map.entry("parentTargetId", "region-seoul"),
                                Map.entry("legalDongCode", "11440"),
                                Map.entry("regionCode", "11440"),
                                Map.entry("source", "test:region-list")
                        ),
                        Map.ofEntries(
                                Map.entry("targetId", "region-test-ahyeon"),
                                Map.entry("displayName", "서울특별시 마포구 아현동"),
                                Map.entry("slug", "test-ahyeon"),
                                Map.entry("regionLevel", "eupmyeondong"),
                                Map.entry("parentTargetId", "region-test-mapo"),
                                Map.entry("legalDongCode", "1144010100"),
                                Map.entry("regionCode", "1144010100"),
                                Map.entry("source", "test:region-list")
                        )
                )
        );

        ResponseEntity<String> importResponse = restTemplate.postForEntity(
                "/internal/realestate/regions",
                request,
                String.class
        );
        ResponseEntity<String> regions = restTemplate.getForEntity(
                "/internal/realestate/regions?regionLevel=eupmyeondong&limit=50",
                String.class
        );

        assertThat(importResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(regions.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode items = objectMapper.readTree(regions.getBody()).path("items");
        assertThat(items)
                .filteredOn(item -> "region-test-ahyeon".equals(item.path("targetId").asText()))
                .singleElement()
                .satisfies(item -> {
                    assertThat(item.path("displayName").asText()).isEqualTo("서울특별시 마포구 아현동");
                    assertThat(item.path("regionLevel").asText()).isEqualTo("eupmyeondong");
                    assertThat(item.path("parentTargetId").asText()).isEqualTo("region-test-mapo");
                    assertThat(item.path("legalDongCode").asText()).isEqualTo("1144010100");
                });
    }
}
