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
class RealEstateDailyBriefingIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void upsertsDailyBriefingAndReturnsLatestNarrativeBriefing() throws Exception {
        Map<String, Object> request = Map.of(
                "briefings",
                List.of(Map.ofEntries(
                        Map.entry("briefingId", "daily-briefing-20260624-v1"),
                        Map.entry("briefingDate", "2026-06-24"),
                        Map.entry("title", "오늘의 부동산 시장 브리핑"),
                        Map.entry("summaryHeadlines", List.of(
                                "수도권 전세 압력 재부각",
                                "서울 동남권 거래 회복 흐름",
                                "경기 남부 공급·정책 이슈 집중"
                        )),
                        Map.entry("sections", List.of(
                                Map.of(
                                        "sectionId", "flow",
                                        "title", "오늘의 핵심 흐름",
                                        "body", "수도권 전세와 거래 회복 흐름이 함께 관찰됩니다.",
                                        "displayOrder", 1
                                ),
                                Map.of(
                                        "sectionId", "regions",
                                        "title", "주목할 지역과 이유",
                                        "body", "서울 동남권과 경기 남부를 함께 확인합니다.",
                                        "displayOrder", 2
                                ),
                                Map.of(
                                        "sectionId", "variables",
                                        "title", "시장 변수",
                                        "body", "공급 일정과 정책 이슈가 지역별 체감 흐름을 가릅니다.",
                                        "displayOrder", 3
                                ),
                                Map.of(
                                        "sectionId", "sources",
                                        "title", "관련 뉴스·리포트",
                                        "body", "관련 리포트는 근거 후보로만 연결합니다.",
                                        "displayOrder", 4
                                )
                        )),
                        Map.entry("focusRegions", List.of(Map.of(
                                "targetId", "region-seoul",
                                "label", "서울",
                                "reason", "거래 회복 흐름",
                                "displayOrder", 1
                        ))),
                        Map.entry("modelName", "claude opus 4 8"),
                        Map.entry("promptVersion", "daily-briefing-v1"),
                        Map.entry("generatedAt", "2026-06-24T00:30:00Z"),
                        Map.entry("sourceItems", List.of(Map.of(
                                "sourceItemId", "source-news-1",
                                "sourceType", "content",
                                "refId", "content-news-briefing",
                                "label", "정책 리포트",
                                "title", "수도권 전세 보고서",
                                "url", "https://example.com/report",
                                "displayOrder", 1
                        )))
                ))
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/daily-briefings",
                request,
                String.class
        );
        ResponseEntity<String> latest = restTemplate.getForEntity(
                "/api/realestate/daily-briefings/latest",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode ingestRoot = objectMapper.readTree(ingest.getBody());
        assertThat(ingestRoot.path("acceptedBriefings").asInt()).isEqualTo(1);
        assertThat(ingestRoot.path("acceptedSections").asInt()).isEqualTo(4);
        assertThat(ingestRoot.path("acceptedSourceItems").asInt()).isEqualTo(1);

        assertThat(latest.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode briefing = objectMapper.readTree(latest.getBody());
        assertThat(briefing.path("briefingId").asText()).isEqualTo("daily-briefing-20260624-v1");
        assertThat(briefing.path("summaryHeadlines")).hasSize(3);
        assertThat(briefing.path("summaryHeadlines").get(0).asText()).isEqualTo("수도권 전세 압력 재부각");
        assertThat(briefing.path("sections")).hasSize(4);
        assertThat(briefing.path("sections").get(0).path("title").asText()).isEqualTo("오늘의 핵심 흐름");
        assertThat(briefing.path("sections").get(1).path("title").asText()).isEqualTo("주목할 지역과 이유");
        assertThat(briefing.path("focusRegions").get(0).path("targetId").asText()).isEqualTo("region-seoul");
        assertThat(briefing.path("sourceItems").get(0).path("url").asText()).isEqualTo("https://example.com/report");
    }

    @Test
    void rejectsDailyBriefingWithoutExactlyThreeHeadlines() {
        Map<String, Object> request = Map.of(
                "briefings",
                List.of(Map.ofEntries(
                        Map.entry("briefingId", "daily-briefing-invalid"),
                        Map.entry("briefingDate", "2026-06-24"),
                        Map.entry("title", "오늘의 부동산 시장 브리핑"),
                        Map.entry("summaryHeadlines", List.of("수도권 전세 압력 재부각", "서울 동남권 거래 회복 흐름")),
                        Map.entry("sections", List.of(Map.of(
                                "sectionId", "flow",
                                "title", "오늘의 핵심 흐름",
                                "body", "수도권 전세와 거래 회복 흐름이 함께 관찰됩니다.",
                                "displayOrder", 1
                        ))),
                        Map.entry("focusRegions", List.of()),
                        Map.entry("generatedAt", "2026-06-24T00:30:00Z"),
                        Map.entry("sourceItems", List.of())
                ))
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/daily-briefings",
                request,
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
    }
}
