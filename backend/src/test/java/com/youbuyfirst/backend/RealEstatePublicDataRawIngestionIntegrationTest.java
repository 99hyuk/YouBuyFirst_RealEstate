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
import java.util.LinkedHashMap;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class RealEstatePublicDataRawIngestionIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void storesImportRunRawItemsAndValidatedStagingFactsIdempotently() throws Exception {
        Map<String, Object> request = Map.of(
                "run", Map.ofEntries(
                        Map.entry("runKey", "molit_apt_trade:11110:202606"),
                        Map.entry("providerDataset", "molit_apt_trade"),
                        Map.entry("runType", "backfill"),
                        Map.entry("requestedFrom", "2026-06-01"),
                        Map.entry("requestedTo", "2026-06-30"),
                        Map.entry("requestParams", Map.of(
                                "LAWD_CD", "11110",
                                "DEAL_YMD", "202606"
                        )),
                        Map.entry("status", "running"),
                        Map.entry("startedAt", "2026-06-12T00:00:00Z")
                ),
                "items", List.of(Map.ofEntries(
                        Map.entry("providerDataset", "molit_apt_trade"),
                        Map.entry("providerObjectId", "molit_apt_trade:11110:202606:raw-1"),
                        Map.entry("legalDongCode", "11110"),
                        Map.entry("targetId", "region-seoul-jongno"),
                        Map.entry("observedAt", "2026-06-03"),
                        Map.entry("asOf", "2026-06-01"),
                        Map.entry("rawPayload", Map.of(
                                "aptNm", "Sajik Palace",
                                "dealAmount", "82,500",
                                "dealYear", "2026",
                                "dealMonth", "6",
                                "dealDay", "3"
                        )),
                        Map.entry("landingStatus", "landed"),
                        Map.entry("staging", Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("legalDongCode", "11110"),
                                Map.entry("factType", "apt_trade"),
                                Map.entry("observedAt", "2026-06-03"),
                                Map.entry("asOf", "2026-06-01"),
                                Map.entry("valueJson", Map.of(
                                        "apartmentName", "Sajik Palace",
                                        "dealAmountManwon", 82500
                                )),
                                Map.entry("validationStatus", "valid")
                        ))
                ))
        );

        ResponseEntity<String> first = restTemplate.postForEntity(
                "/internal/realestate/public-data/raw-ingestions",
                request,
                String.class
        );
        ResponseEntity<String> duplicate = restTemplate.postForEntity(
                "/internal/realestate/public-data/raw-ingestions",
                request,
                String.class
        );

        assertThat(first.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(duplicate.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode firstBody = objectMapper.readTree(first.getBody());
        JsonNode duplicateBody = objectMapper.readTree(duplicate.getBody());
        assertThat(firstBody.path("runId").asLong()).isPositive();
        assertThat(firstBody.path("acceptedRawItems").asInt()).isEqualTo(1);
        assertThat(firstBody.path("acceptedStagingItems").asInt()).isEqualTo(1);
        assertThat(duplicateBody.path("runId").asLong()).isEqualTo(firstBody.path("runId").asLong());
        assertThat(duplicateBody.path("acceptedRawItems").asInt()).isEqualTo(1);
        assertThat(duplicateBody.path("acceptedStagingItems").asInt()).isEqualTo(1);

        ResponseEntity<String> listed = restTemplate.getForEntity(
                "/internal/realestate/public-data/import-runs?providerDataset=molit_apt_trade",
                String.class
        );

        assertThat(listed.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(listed.getBody()).path("items");
        JsonNode importRun = findRunByKey(items, "molit_apt_trade:11110:202606");
        assertThat(importRun).isNotNull();
        assertThat(importRun.path("providerDataset").asText()).isEqualTo("molit_apt_trade");
        assertThat(importRun.path("rowsLanded").asLong()).isEqualTo(1);
        assertThat(importRun.path("rowsStaged").asLong()).isEqualTo(1);
    }

    @Test
    void storesEmptyImportRunWhenProviderReturnsNoRows() throws Exception {
        Map<String, Object> request = Map.of(
                "run", Map.ofEntries(
                        Map.entry("runKey", "molit_apt_rent:11680:202605"),
                        Map.entry("providerDataset", "molit_apt_rent"),
                        Map.entry("runType", "backfill"),
                        Map.entry("requestedFrom", "2026-05-01"),
                        Map.entry("requestedTo", "2026-05-31"),
                        Map.entry("requestParams", Map.of(
                                "LAWD_CD", "11680",
                                "DEAL_YMD", "202505"
                        )),
                        Map.entry("status", "completed"),
                        Map.entry("startedAt", "2026-06-12T00:00:00Z"),
                        Map.entry("finishedAt", "2026-06-12T00:01:00Z")
                ),
                "items", List.of()
        );

        ResponseEntity<String> response = restTemplate.postForEntity(
                "/internal/realestate/public-data/raw-ingestions",
                request,
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode body = objectMapper.readTree(response.getBody());
        assertThat(body.path("acceptedRawItems").asInt()).isZero();
        assertThat(body.path("acceptedStagingItems").asInt()).isZero();

        ResponseEntity<String> listed = restTemplate.getForEntity(
                "/internal/realestate/public-data/import-runs?providerDataset=molit_apt_rent",
                String.class
        );

        JsonNode items = objectMapper.readTree(listed.getBody()).path("items");
        JsonNode emptyRun = null;
        for (JsonNode item : items) {
            if ("molit_apt_rent:11680:202605".equals(item.path("runKey").asText())) {
                emptyRun = item;
                break;
            }
        }
        assertThat(emptyRun).isNotNull();
        assertThat(emptyRun.path("rowsLanded").asLong()).isZero();
        assertThat(emptyRun.path("rowsStaged").asLong()).isZero();
    }

    @Test
    void listsImportRunsByExplicitRunKeysForBackfillResume() throws Exception {
        postEmptyCompletedRun("molit_apt_trade:11110:202607", "molit_apt_trade", "11110", "202607");
        postEmptyCompletedRun("molit_apt_trade:11110:202608", "molit_apt_trade", "11110", "202608");
        postEmptyCompletedRun("molit_apt_trade:11110:202609", "molit_apt_trade", "11110", "202609");

        ResponseEntity<String> listed = restTemplate.getForEntity(
                "/internal/realestate/public-data/import-runs"
                        + "?status=completed"
                        + "&runKey=molit_apt_trade:11110:202607"
                        + "&runKey=molit_apt_trade:11110:202608",
                String.class
        );

        assertThat(listed.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(listed.getBody()).path("items");
        assertThat(items).hasSize(2);
        assertThat(items.get(0).path("runKey").asText()).isEqualTo("molit_apt_trade:11110:202607");
        assertThat(items.get(1).path("runKey").asText()).isEqualTo("molit_apt_trade:11110:202608");
    }

    @Test
    void promotesValidatedStagingFactsIntoMarketFactsAndUpdatesRunProgress() throws Exception {
        Map<String, Object> request = Map.of(
                "run", Map.ofEntries(
                        Map.entry("runKey", "molit_apt_rent:11110:202606"),
                        Map.entry("providerDataset", "molit_apt_rent"),
                        Map.entry("runType", "backfill"),
                        Map.entry("requestedFrom", "2026-06-01"),
                        Map.entry("requestedTo", "2026-06-30"),
                        Map.entry("requestParams", Map.of(
                                "LAWD_CD", "11110",
                                "DEAL_YMD", "202606"
                        )),
                        Map.entry("status", "succeeded"),
                        Map.entry("startedAt", "2026-06-12T00:00:00Z"),
                        Map.entry("finishedAt", "2026-06-12T00:01:00Z")
                ),
                "items", List.of(Map.ofEntries(
                        Map.entry("providerDataset", "molit_apt_rent"),
                        Map.entry("providerObjectId", "molit_apt_rent:11110:202606:raw-1"),
                        Map.entry("legalDongCode", "11110"),
                        Map.entry("targetId", "region-seoul-jongno"),
                        Map.entry("observedAt", "2026-06-04"),
                        Map.entry("asOf", "2026-06-01"),
                        Map.entry("rawPayload", Map.of(
                                "aptNm", "Sajik Palace",
                                "deposit", "45,000",
                                "monthlyRent", "120",
                                "dealYear", "2026",
                                "dealMonth", "6",
                                "dealDay", "4"
                        )),
                        Map.entry("landingStatus", "landed"),
                        Map.entry("staging", Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("legalDongCode", "11110"),
                                Map.entry("factType", "apt_rent"),
                                Map.entry("observedAt", "2026-06-04"),
                                Map.entry("asOf", "2026-06-01"),
                                Map.entry("valueJson", Map.of(
                                        "apartmentName", "Sajik Palace",
                                        "depositManwon", 45000,
                                        "monthlyRentManwon", 120
                                )),
                                Map.entry("validationStatus", "valid")
                        ))
                ))
        );

        ResponseEntity<String> ingested = restTemplate.postForEntity(
                "/internal/realestate/public-data/raw-ingestions",
                request,
                String.class
        );
        assertThat(ingested.getStatusCode()).isEqualTo(HttpStatus.OK);

        Map<String, Object> promoteRequest = Map.of(
                "providerDataset", "molit_apt_rent",
                "runKey", "molit_apt_rent:11110:202606",
                "validationStatus", "valid",
                "limit", 10
        );
        ResponseEntity<String> promoted = restTemplate.postForEntity(
                "/internal/realestate/public-data/promote-staging",
                promoteRequest,
                String.class
        );

        assertThat(promoted.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode promotedBody = objectMapper.readTree(promoted.getBody());
        assertThat(promotedBody.path("promotedFacts").asInt()).isEqualTo(1);

        ResponseEntity<String> marketFacts = restTemplate.getForEntity(
                "/api/realestate/market-facts?legalDongCode=11110&factType=apt_rent",
                String.class
        );
        assertThat(marketFacts.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode facts = objectMapper.readTree(marketFacts.getBody()).path("items");
        assertThat(facts).hasSize(1);
        assertThat(facts.get(0).path("provider").asText()).isEqualTo("molit");
        assertThat(facts.get(0).path("providerDataset").asText()).isEqualTo("molit_apt_rent");
        assertThat(facts.get(0).path("providerObjectId").asText())
                .isEqualTo("molit_apt_rent:11110:202606:raw-1");
        assertThat(facts.get(0).path("valueJson").path("depositManwon").asInt()).isEqualTo(45000);
        assertThat(facts.get(0).path("dataStatus").asText()).isEqualTo("ok");
        assertThat(facts.get(0).path("stale").asBoolean()).isFalse();

        ResponseEntity<String> listed = restTemplate.getForEntity(
                "/internal/realestate/public-data/import-runs?providerDataset=molit_apt_rent",
                String.class
        );
        JsonNode runs = objectMapper.readTree(listed.getBody()).path("items");
        assertThat(runs).hasSize(1);
        assertThat(runs.get(0).path("rowsPromoted").asLong()).isEqualTo(1);
    }

    @Test
    void importedRegionTargetsCanDriveRawIngestionPromotionAndTargetQueries() throws Exception {
        Map<String, Object> regionImportRequest = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetId", "region-daegu"),
                                Map.entry("displayName", "대구광역시"),
                                Map.entry("slug", "daegu"),
                                Map.entry("regionLevel", "sido"),
                                Map.entry("legalDongCode", "27000"),
                                Map.entry("regionCode", "27"),
                                Map.entry("source", "test:legal-dong-code")
                        ),
                        Map.ofEntries(
                                Map.entry("targetId", "region-daegu-suseong"),
                                Map.entry("displayName", "대구 수성구"),
                                Map.entry("slug", "daegu-suseong"),
                                Map.entry("regionLevel", "sigungu"),
                                Map.entry("parentTargetId", "region-daegu"),
                                Map.entry("legalDongCode", "27260"),
                                Map.entry("regionCode", "27260"),
                                Map.entry("source", "test:legal-dong-code")
                        )
                )
        );

        ResponseEntity<String> imported = restTemplate.postForEntity(
                "/internal/realestate/regions",
                regionImportRequest,
                String.class
        );
        assertThat(imported.getStatusCode()).isEqualTo(HttpStatus.OK);

        ResponseEntity<String> marketDataTargets = restTemplate.getForEntity(
                "/internal/realestate/market-data-targets?enabled=true&limit=500",
                String.class
        );
        JsonNode targetRows = objectMapper.readTree(marketDataTargets.getBody()).path("items");
        assertThat(targetRows)
                .filteredOn(item -> "region-daegu-suseong".equals(item.path("targetId").asText()))
                .extracting(item -> item.path("providerDataset").asText())
                .containsExactlyInAnyOrder("molit_apt_trade", "molit_apt_rent");

        Map<String, Object> rawItem = new LinkedHashMap<>();
        rawItem.put("providerDataset", "molit_apt_trade");
        rawItem.put("providerObjectId", "molit_apt_trade:27260:202606:imported-region-target");
        rawItem.put("legalDongCode", "27260");
        rawItem.put("targetId", null);
        rawItem.put("observedAt", "2026-06-07");
        rawItem.put("asOf", "2026-06-01");
        rawItem.put("rawPayload", Map.of(
                "aptNm", "Suseong Lake Apt",
                "dealAmount", "91,000",
                "dealYear", "2026",
                "dealMonth", "6",
                "dealDay", "7"
        ));
        rawItem.put("landingStatus", "landed");

        Map<String, Object> staging = new LinkedHashMap<>();
        staging.put("targetType", "region");
        staging.put("targetId", null);
        staging.put("legalDongCode", "27260");
        staging.put("factType", "apt_trade");
        staging.put("observedAt", "2026-06-07");
        staging.put("asOf", "2026-06-01");
        staging.put("valueJson", Map.of(
                "apartmentName", "Suseong Lake Apt",
                "dealAmountManwon", 91000
        ));
        staging.put("validationStatus", "valid");
        rawItem.put("staging", staging);

        Map<String, Object> rawIngestionRequest = Map.of(
                "run", Map.ofEntries(
                        Map.entry("runKey", "molit_apt_trade:27260:202606"),
                        Map.entry("providerDataset", "molit_apt_trade"),
                        Map.entry("runType", "backfill"),
                        Map.entry("requestedFrom", "2026-06-01"),
                        Map.entry("requestedTo", "2026-06-30"),
                        Map.entry("requestParams", Map.of(
                                "LAWD_CD", "27260",
                                "DEAL_YMD", "202606"
                        )),
                        Map.entry("status", "completed"),
                        Map.entry("startedAt", "2026-06-12T01:00:00Z"),
                        Map.entry("finishedAt", "2026-06-12T01:01:00Z")
                ),
                "items", List.of(rawItem)
        );

        ResponseEntity<String> ingested = restTemplate.postForEntity(
                "/internal/realestate/public-data/raw-ingestions",
                rawIngestionRequest,
                String.class
        );
        assertThat(ingested.getStatusCode()).isEqualTo(HttpStatus.OK);

        ResponseEntity<String> promoted = restTemplate.postForEntity(
                "/internal/realestate/public-data/promote-staging",
                Map.of(
                        "providerDataset", "molit_apt_trade",
                        "runKey", "molit_apt_trade:27260:202606",
                        "validationStatus", "valid",
                        "limit", 10
                ),
                String.class
        );
        assertThat(promoted.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(objectMapper.readTree(promoted.getBody()).path("promotedFacts").asInt()).isEqualTo(1);

        ResponseEntity<String> factsForTarget = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/market-facts?factType=apt_trade&limit=5",
                String.class,
                "region-daegu-suseong"
        );
        JsonNode facts = objectMapper.readTree(factsForTarget.getBody()).path("items");
        assertThat(facts).hasSize(1);
        assertThat(facts.get(0).path("targetId").asText()).isEqualTo("region-daegu-suseong");
        assertThat(facts.get(0).path("legalDongCode").asText()).isEqualTo("27260");
        assertThat(facts.get(0).path("providerObjectId").asText())
                .isEqualTo("molit_apt_trade:27260:202606:imported-region-target");
        assertThat(facts.get(0).path("valueJson").path("dealAmountManwon").asInt()).isEqualTo(91000);
    }

    private void postEmptyCompletedRun(
            String runKey,
            String providerDataset,
            String lawdCode,
            String dealYm
    ) {
        String requestedFrom = dealYm.substring(0, 4) + "-" + dealYm.substring(4) + "-01";
        String requestedTo = dealYm.substring(0, 4) + "-" + dealYm.substring(4) + "-28";
        Map<String, Object> request = Map.of(
                "run", Map.ofEntries(
                        Map.entry("runKey", runKey),
                        Map.entry("providerDataset", providerDataset),
                        Map.entry("runType", "backfill"),
                        Map.entry("requestedFrom", requestedFrom),
                        Map.entry("requestedTo", requestedTo),
                        Map.entry("requestParams", Map.of(
                                "LAWD_CD", lawdCode,
                                "DEAL_YMD", dealYm
                        )),
                        Map.entry("status", "completed"),
                        Map.entry("startedAt", "2026-06-12T00:00:00Z"),
                        Map.entry("finishedAt", "2026-06-12T00:01:00Z")
                ),
                "items", List.of()
        );

        ResponseEntity<String> response = restTemplate.postForEntity(
                "/internal/realestate/public-data/raw-ingestions",
                request,
                String.class
        );
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
    }

    private static JsonNode findRunByKey(JsonNode runs, String runKey) {
        for (JsonNode run : runs) {
            if (runKey.equals(run.path("runKey").asText())) {
                return run;
            }
        }
        return null;
    }
}
