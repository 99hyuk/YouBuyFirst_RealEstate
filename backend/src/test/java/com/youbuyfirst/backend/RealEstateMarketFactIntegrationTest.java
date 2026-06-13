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
class RealEstateMarketFactIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void ingestsRealEstateMarketFactsIdempotentlyAndListsByLegalDongAndFactType() throws Exception {
        Map<String, Object> firstRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetType", "region"),
                        Map.entry("targetId", "region-seoul-jongno"),
                        Map.entry("factType", "apt_trade"),
                        Map.entry("provider", "molit"),
                        Map.entry("providerDataset", "molit_apt_trade"),
                        Map.entry("providerObjectId", "molit_apt_trade:11110:202606:sample"),
                        Map.entry("legalDongCode", "11110"),
                        Map.entry("observedAt", "2026-06-03"),
                        Map.entry("asOf", "2026-06-01"),
                        Map.entry("ingestedAt", "2026-06-11T00:05:00Z"),
                        Map.entry("sourceUpdatedAt", "2026-06-11T00:00:00Z"),
                        Map.entry("dataStatus", "ok"),
                        Map.entry("stale", false),
                        Map.entry("valueJson", Map.of(
                                "apartmentName", "Sajik Palace",
                                "dealAmountManwon", 82500,
                                "exclusiveAreaM2", 84.97,
                                "raw", Map.of("dealAmount", "82,500")
                        ))
                ))
        );
        Map<String, Object> duplicateRequest = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("targetType", "region"),
                        Map.entry("targetId", "region-seoul-jongno"),
                        Map.entry("factType", "apt_trade"),
                        Map.entry("provider", "molit"),
                        Map.entry("providerDataset", "molit_apt_trade"),
                        Map.entry("providerObjectId", "molit_apt_trade:11110:202606:sample"),
                        Map.entry("legalDongCode", "11110"),
                        Map.entry("observedAt", "2026-06-03"),
                        Map.entry("asOf", "2026-06-01"),
                        Map.entry("ingestedAt", "2026-06-11T00:10:00Z"),
                        Map.entry("dataStatus", "ok"),
                        Map.entry("stale", false),
                        Map.entry("valueJson", Map.of(
                                "apartmentName", "Sajik Palace",
                                "dealAmountManwon", 83000,
                                "exclusiveAreaM2", 84.97
                        ))
                ))
        );

        ResponseEntity<String> first = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                firstRequest,
                String.class
        );
        ResponseEntity<String> duplicate = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                duplicateRequest,
                String.class
        );

        assertThat(first.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(duplicate.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(first.getBody()).contains("\"acceptedFacts\":1");
        assertThat(duplicate.getBody()).contains("\"acceptedFacts\":1");

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/market-facts?legalDongCode=11110&factType=apt_trade",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(response.getBody()).path("items");
        assertThat(items).hasSize(1);
        JsonNode fact = items.get(0);
        assertThat(fact.path("targetType").asText()).isEqualTo("region");
        assertThat(fact.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(fact.path("factType").asText()).isEqualTo("apt_trade");
        assertThat(fact.path("provider").asText()).isEqualTo("molit");
        assertThat(fact.path("providerDataset").asText()).isEqualTo("molit_apt_trade");
        assertThat(fact.path("providerObjectId").asText()).isEqualTo("molit_apt_trade:11110:202606:sample");
        assertThat(fact.path("legalDongCode").asText()).isEqualTo("11110");
        assertThat(fact.path("observedAt").asText()).isEqualTo("2026-06-03");
        assertThat(fact.path("asOf").asText()).isEqualTo("2026-06-01");
        assertThat(fact.path("ingestedAt").asText()).isEqualTo("2026-06-11T00:10:00Z");
        assertThat(fact.path("sourceUpdatedAt").isNull()).isTrue();
        assertThat(fact.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(fact.path("stale").asBoolean()).isFalse();
        assertThat(fact.path("valueJson").path("apartmentName").asText()).isEqualTo("Sajik Palace");
        assertThat(fact.path("valueJson").path("dealAmountManwon").asInt()).isEqualTo(83000);
    }

    @Test
    void summarizesLatestMarketFactsForDashboardCards() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("factType", "apt_trade"),
                                Map.entry("provider", "molit"),
                                Map.entry("providerDataset", "molit_apt_trade"),
                                Map.entry("providerObjectId", "molit_apt_trade:11680:202606:summary-trade"),
                                Map.entry("legalDongCode", "11680"),
                                Map.entry("observedAt", "2026-06-09"),
                                Map.entry("asOf", "2026-06-01"),
                                Map.entry("ingestedAt", "2026-06-11T00:15:00Z"),
                                Map.entry("dataStatus", "ok"),
                                Map.entry("stale", false),
                                Map.entry("valueJson", Map.of(
                                        "apartmentName", "Sajik Palace",
                                        "dealAmountManwon", 82500,
                                        "exclusiveAreaM2", 84.97
                                ))
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("factType", "apt_rent"),
                                Map.entry("provider", "molit"),
                                Map.entry("providerDataset", "molit_apt_rent"),
                                Map.entry("providerObjectId", "molit_apt_rent:11680:202606:summary-rent"),
                                Map.entry("legalDongCode", "11680"),
                                Map.entry("observedAt", "2026-06-10"),
                                Map.entry("asOf", "2026-06-01"),
                                Map.entry("ingestedAt", "2026-06-11T00:20:00Z"),
                                Map.entry("dataStatus", "ok"),
                                Map.entry("stale", false),
                                Map.entry("valueJson", Map.of(
                                        "apartmentName", "Sajik Palace",
                                        "depositManwon", 45000,
                                        "monthlyRentManwon", 120,
                                        "exclusiveAreaM2", 84.97
                                ))
                        )
                )
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                request,
                String.class
        );
        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/dashboard/market-summary?legalDongCode=11680",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode root = objectMapper.readTree(response.getBody());
        assertThat(root.path("items")).hasSize(2);
        assertThat(root.path("items").get(0).path("label").asText()).isEqualTo("매매 실거래");
        assertThat(root.path("items").get(0).path("value").asText()).isEqualTo("8.25억원");
        assertThat(root.path("items").get(0).path("updatedLabel").asText())
                .isEqualTo("국토교통부 · 계약 2026-06-09 · 기준 2026-06-01");
        assertThat(root.path("items").get(1).path("label").asText()).isEqualTo("전월세 실거래");
        assertThat(root.path("items").get(1).path("value").asText()).isEqualTo("보증금 4.50억원 / 월세 120만원");
        assertThat(root.path("freshness").path("latestAsOf").asText()).isEqualTo("2026-06-01");
        assertThat(root.path("freshness").path("sourceCount").asInt()).isEqualTo(1);
        assertThat(root.path("freshness").path("staleCount").asInt()).isZero();
        assertThat(root.path("freshness").path("dataStatus").asText()).isEqualTo("ok");
    }

    @Test
    void listsTargetMarketFactsForDetailTimeline() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul-jongno"),
                                Map.entry("factType", "listing_count"),
                                Map.entry("provider", "manual"),
                                Map.entry("providerDataset", "manual_listing_count"),
                                Map.entry("providerObjectId", "manual_listing_count:11110:202606:detail-target"),
                                Map.entry("legalDongCode", "11110"),
                                Map.entry("observedAt", "2026-06-12"),
                                Map.entry("asOf", "2026-06-12"),
                                Map.entry("ingestedAt", "2026-06-12T01:10:00Z"),
                                Map.entry("dataStatus", "partial"),
                                Map.entry("stale", false),
                                Map.entry("valueJson", Map.of(
                                        "listingCount", 132,
                                        "basis", "manual-import"
                                ))
                        ),
                        Map.ofEntries(
                                Map.entry("targetType", "region"),
                                Map.entry("targetId", "region-seoul"),
                                Map.entry("factType", "listing_count"),
                                Map.entry("provider", "manual"),
                                Map.entry("providerDataset", "manual_listing_count"),
                                Map.entry("providerObjectId", "manual_listing_count:11000:202606:other-target"),
                                Map.entry("legalDongCode", "11000"),
                                Map.entry("observedAt", "2026-06-12"),
                                Map.entry("asOf", "2026-06-12"),
                                Map.entry("ingestedAt", "2026-06-12T01:10:00Z"),
                                Map.entry("dataStatus", "ok"),
                                Map.entry("stale", false),
                                Map.entry("valueJson", Map.of("listingCount", 420))
                        )
                )
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                request,
                String.class
        );
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/market-facts?factType=listing_count&limit=5",
                String.class,
                "region-seoul-jongno"
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(response.getBody()).path("items");
        assertThat(items).hasSize(1);
        JsonNode fact = items.get(0);
        assertThat(fact.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(fact.path("factType").asText()).isEqualTo("listing_count");
        assertThat(fact.path("observedAt").asText()).isEqualTo("2026-06-12");
        assertThat(fact.path("valueJson").path("listingCount").asInt()).isEqualTo(132);
        assertThat(fact.path("dataStatus").asText()).isEqualTo("partial");
    }
}
