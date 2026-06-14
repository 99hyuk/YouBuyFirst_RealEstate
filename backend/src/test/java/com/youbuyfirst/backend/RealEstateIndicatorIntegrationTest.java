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
class RealEstateIndicatorIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void exposesIndicatorOverviewFromLiveMarketFactsWithoutHidingFreshness() throws Exception {
        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/market-facts",
                Map.of(
                        "items",
                        List.of(
                                Map.ofEntries(
                                        Map.entry("targetType", "region"),
                                        Map.entry("factType", "apt_trade"),
                                        Map.entry("provider", "molit"),
                                        Map.entry("providerDataset", "molit_apt_trade"),
                                        Map.entry("providerObjectId", "molit_apt_trade:11740:202606:indicator-trade"),
                                        Map.entry("legalDongCode", "11740"),
                                        Map.entry("observedAt", "2026-06-09"),
                                        Map.entry("asOf", "2026-06-01"),
                                        Map.entry("ingestedAt", "2026-06-12T00:15:00Z"),
                                        Map.entry("dataStatus", "ok"),
                                        Map.entry("stale", false),
                                        Map.entry("valueJson", Map.of(
                                                "apartmentName", "Gangdong Indicator Sample",
                                                "dealAmountManwon", 91500
                                        ))
                                ),
                                Map.ofEntries(
                                        Map.entry("targetType", "region"),
                                        Map.entry("factType", "apt_rent"),
                                        Map.entry("provider", "molit"),
                                        Map.entry("providerDataset", "molit_apt_rent"),
                                        Map.entry("providerObjectId", "molit_apt_rent:11740:202606:indicator-rent"),
                                        Map.entry("legalDongCode", "11740"),
                                        Map.entry("observedAt", "2026-06-10"),
                                        Map.entry("asOf", "2026-06-01"),
                                        Map.entry("ingestedAt", "2026-06-12T00:20:00Z"),
                                        Map.entry("dataStatus", "ok"),
                                        Map.entry("stale", false),
                                        Map.entry("valueJson", Map.of(
                                                "apartmentName", "Gangdong Indicator Sample",
                                                "depositManwon", 52000,
                                                "monthlyRentManwon", 135
                                        ))
                                )
                        )
                ),
                String.class
        );

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/indicators?legalDongCode=11740&period=month",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode root = objectMapper.readTree(response.getBody());
        assertThat(root.path("period").asText()).isEqualTo("month");
        assertThat(root.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(root.path("asOf").asText()).isEqualTo("2026-06-01");

        JsonNode groups = root.path("groups");
        assertThat(groups).hasSize(1);
        JsonNode priceGroup = groups.get(0);
        assertThat(priceGroup.path("id").asText()).isEqualTo("price-transaction");
        assertThat(priceGroup.path("title").asText()).isEqualTo("가격 및 거래량");
        assertThat(priceGroup.path("change").asText()).isEqualTo("최신");
        assertThat(priceGroup.path("tone").asText()).isEqualTo("up");
        assertThat(priceGroup.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(priceGroup.path("stale").asBoolean()).isFalse();
        assertThat(priceGroup.path("provider").asText()).isEqualTo("molit");
        assertThat(priceGroup.path("asOf").asText()).isEqualTo("2026-06-01");
        assertThat(priceGroup.path("chips"))
                .extracting(JsonNode::asText)
                .contains("매매 실거래 9.15억원", "전월세 실거래 보증금 5.20억원 / 월세 135만원");
        assertThat(priceGroup.path("metrics")).hasSize(2);
        assertThat(priceGroup.path("metrics").get(0).path("name").asText()).isEqualTo("매매 실거래");
        assertThat(priceGroup.path("metrics").get(0).path("value").asText()).isEqualTo("9.15억원");

        JsonNode freshnessRows = root.path("freshnessRows");
        assertThat(freshnessRows).hasSize(1);
        assertThat(freshnessRows.get(0).path("source").asText()).isEqualTo("국토부 실거래가");
        assertThat(freshnessRows.get(0).path("state").asText()).isEqualTo("공공데이터 반영");
        assertThat(freshnessRows.get(0).path("used").asText()).isEqualTo("매매/전월세 실거래");
    }
}
