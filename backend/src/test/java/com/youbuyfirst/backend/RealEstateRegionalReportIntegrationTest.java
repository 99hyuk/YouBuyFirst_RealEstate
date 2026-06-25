package com.youbuyfirst.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class RealEstateRegionalReportIntegrationTest {

    private static final String FINANCIAL_OUTLOOK_GENERATOR = "codex-quality-rewrite:financial-outlook-20260625";
    private static final List<String> FORBIDDEN_POINT_WORDS = List.of(
            "합니다",
            "됩니다",
            "습니다",
            "있습니다",
            "수 있습니다",
            "."
    );
    private static final List<String> OUTLOOK_WORDS = List.of("관망", "선별", "상승 지속 가능성", "보수적");

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    @Order(1)
    void servesResearchedLatestReportForEveryRegionAndSigunguTarget() throws Exception {
        ResponseEntity<String> mapo = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-seoul-mapo"
        );
        ResponseEntity<String> haeundae = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-busan-haeundae"
        );

        assertThat(mapo.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode mapoRoot = objectMapper.readTree(mapo.getBody());
        assertThat(mapoRoot.path("targetId").asText()).isEqualTo("region-seoul-mapo");
        assertThat(mapoRoot.path("regionLevel").asText()).isEqualTo("sigungu");
        assertThat(mapoRoot.path("generatedBy").asText()).isEqualTo(FINANCIAL_OUTLOOK_GENERATOR);
        assertThat(mapoRoot.path("title").asText()).isNotBlank();
        assertThat(mapoRoot.path("body").asText()).isNotBlank();
        assertThat(mapoRoot.path("expectationPoints")).hasSizeBetween(1, 2);
        assertThat(mapoRoot.path("concernPoints")).hasSizeBetween(1, 2);
        assertThat(mapoRoot.path("sources")).hasSizeGreaterThanOrEqualTo(6);
        assertThat(mapoRoot.path("sources").get(0).path("title").asText()).isNotBlank();

        assertThat(haeundae.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode haeundaeRoot = objectMapper.readTree(haeundae.getBody());
        assertThat(haeundaeRoot.path("targetId").asText()).isEqualTo("region-busan-haeundae");
        assertThat(haeundaeRoot.path("regionLevel").asText()).isEqualTo("sigungu");
        assertThat(haeundaeRoot.path("body").asText()).contains("해운대");
    }

    @Test
    @Order(2)
    void seoulReportsUseDeepResearchSynthesisInsteadOfGenericFacts() throws Exception {
        ResponseEntity<String> seoul = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-seoul"
        );
        ResponseEntity<String> seocho = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-seoul-seocho"
        );
        ResponseEntity<String> mapo = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-seoul-mapo"
        );
        ResponseEntity<String> nowon = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-seoul-nowon"
        );

        assertThat(seoul.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode seoulRoot = objectMapper.readTree(seoul.getBody());
        assertThat(seoulRoot.path("generatedBy").asText()).isEqualTo(FINANCIAL_OUTLOOK_GENERATOR);
        assertThat(seoulRoot.path("body").asText()).contains("강남3구와 용산");
        assertThat(seoulRoot.path("body").asText()).contains("서리풀2지구 2,000호");
        assertThat(seoulRoot.path("body").asText()).contains("전세 압력");

        assertThat(seocho.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode seochoRoot = objectMapper.readTree(seocho.getBody());
        assertThat(seochoRoot.path("body").asText()).contains("서리풀2지구");
        assertThat(seochoRoot.path("concernPoints").toString()).contains("토지거래허가");

        assertThat(mapo.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode mapoRoot = objectMapper.readTree(mapo.getBody());
        assertThat(mapoRoot.path("body").asText()).contains("상암·공덕·홍대");
        assertThat(mapoRoot.path("body").asText()).contains("강남권 대체재");

        assertThat(nowon.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode nowonRoot = objectMapper.readTree(nowon.getBody());
        assertThat(nowonRoot.path("body").asText()).contains("노후 단지");
        assertThat(nowonRoot.path("body").asText()).contains("재건축 기대와 실수요 가격대");
    }

    @Test
    @Order(3)
    void gyeonggiAndIncheonReportsUseDeepResearchSynthesis() throws Exception {
        ResponseEntity<String> gyeonggi = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-gyeonggi"
        );
        ResponseEntity<String> yonginCheoin = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-gyeonggi-yonginsicheoingu"
        );
        ResponseEntity<String> bucheon = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-gyeonggi-bucheon"
        );
        ResponseEntity<String> incheonGyeyang = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-incheon-gyeyang"
        );

        assertThat(gyeonggi.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode gyeonggiRoot = objectMapper.readTree(gyeonggi.getBody());
        assertThat(gyeonggiRoot.path("generatedBy").asText())
                .isEqualTo(FINANCIAL_OUTLOOK_GENERATOR);
        assertThat(gyeonggiRoot.path("body").asText()).contains("1기 신도시 정비");
        assertThat(gyeonggiRoot.path("body").asText()).contains("3기 신도시");
        assertThat(gyeonggiRoot.path("body").asText()).contains("용인 반도체");

        assertThat(yonginCheoin.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode yonginRoot = objectMapper.readTree(yonginCheoin.getBody());
        assertThat(yonginRoot.path("body").asText()).contains("첨단시스템반도체 국가산단");
        assertThat(yonginRoot.path("concernPoints").toString()).contains("산업 뉴스");

        assertThat(bucheon.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode bucheonRoot = objectMapper.readTree(bucheon.getBody());
        assertThat(bucheonRoot.path("body").asText()).contains("부천대장");
        assertThat(bucheonRoot.path("body").asText()).contains("중동 1기 신도시");

        assertThat(incheonGyeyang.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode gyeyangRoot = objectMapper.readTree(incheonGyeyang.getBody());
        assertThat(gyeyangRoot.path("body").asText()).contains("계양테크노밸리");
        assertThat(gyeyangRoot.path("body").asText()).contains("17천호");
        assertThat(gyeyangRoot.path("sources")).hasSizeGreaterThanOrEqualTo(8);
    }

    @Test
    @Order(4)
    void allRegionalReportsUseDeepResearchAfterNationwideBatches() throws Exception {
        Integer regionCount = jdbcTemplate.queryForObject(
                """
                select count(*)
                from real_estate_regions
                where region_level in ('sido', 'sigungu')
                  and source like 'seed:%'
                """,
                Integer.class
        );
        Integer deepReportCount = jdbcTemplate.queryForObject(
                """
                select count(*)
                from real_estate_regional_reports report
                join real_estate_regions region on region.target_id = report.target_id
                where report.data_quality = 'deep_researched'
                  and region.region_level in ('sido', 'sigungu')
                  and region.source like 'seed:%'
                """,
                Integer.class
        );
        Integer genericReportCount = jdbcTemplate.queryForObject(
                "select count(*) from real_estate_regional_reports where generated_by = 'codex-research:regional-report-20260624'",
                Integer.class
        );

        ResponseEntity<String> busanHaeundae = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-busan-haeundae"
        );
        ResponseEntity<String> daeguSuseong = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-daegu-suseong"
        );
        ResponseEntity<String> sejong = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-sejong"
        );
        ResponseEntity<String> jeju = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-jeju-jeju"
        );

        assertThat(deepReportCount).isEqualTo(regionCount);
        assertThat(genericReportCount).isZero();

        assertThat(busanHaeundae.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode busanRoot = objectMapper.readTree(busanHaeundae.getBody());
        assertThat(busanRoot.path("generatedBy").asText()).isEqualTo(FINANCIAL_OUTLOOK_GENERATOR);
        assertThat(busanRoot.path("body").asText()).contains("북항");
        assertThat(busanRoot.path("body").asText()).contains("해운대");

        assertThat(daeguSuseong.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode daeguRoot = objectMapper.readTree(daeguSuseong.getBody());
        assertThat(daeguRoot.path("body").asText()).contains("미분양");
        assertThat(daeguRoot.path("body").asText()).contains("수성구");

        assertThat(sejong.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode sejongRoot = objectMapper.readTree(sejong.getBody());
        assertThat(sejongRoot.path("body").asText()).contains("행정수도");
        assertThat(sejongRoot.path("body").asText()).contains("5생활권");

        assertThat(jeju.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode jejuRoot = objectMapper.readTree(jeju.getBody());
        assertThat(jejuRoot.path("body").asText()).contains("관광");
        assertThat(jejuRoot.path("body").asText()).contains("주택 통계");
    }

    @Test
    @Order(5)
    void investorColumnRewriteRemovesBoilerplateAndDifferentiatesLocalReports() throws Exception {
        ResponseEntity<String> chungnam = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-chungnam"
        );
        ResponseEntity<String> asan = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-chungnam-asan"
        );
        ResponseEntity<String> cheonanSeobuk = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-chungnam-cheonansiseobukgu"
        );
        ResponseEntity<String> dangjin = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-chungnam-dangjinsi"
        );

        assertThat(chungnam.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(asan.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(cheonanSeobuk.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(dangjin.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode chungnamRoot = objectMapper.readTree(chungnam.getBody());
        JsonNode asanRoot = objectMapper.readTree(asan.getBody());
        JsonNode cheonanRoot = objectMapper.readTree(cheonanSeobuk.getBody());
        JsonNode dangjinRoot = objectMapper.readTree(dangjin.getBody());

        assertThat(chungnamRoot.path("generatedBy").asText()).isEqualTo(FINANCIAL_OUTLOOK_GENERATOR);
        assertThat(chungnamRoot.path("body").asText()).contains("천안·아산");
        assertThat(chungnamRoot.path("body").asText()).contains("서해안 산업축");

        assertThat(asanRoot.path("body").asText()).contains("아산");
        assertThat(asanRoot.path("body").asText()).contains("천안과 붙어 있는 수요");
        assertThat(cheonanRoot.path("body").asText()).contains("서북구");
        assertThat(cheonanRoot.path("body").asText()).contains("수도권 남부 출퇴근");
        assertThat(dangjinRoot.path("body").asText()).contains("당진");
        assertThat(dangjinRoot.path("body").asText()).contains("제철·항만");

        assertThat(asanRoot.path("body").asText()).isNotEqualTo(cheonanRoot.path("body").asText());
        assertThat(asanRoot.path("body").asText()).isNotEqualTo(dangjinRoot.path("body").asText());

        for (JsonNode report : List.of(chungnamRoot, asanRoot, cheonanRoot, dangjinRoot)) {
            assertThat(report.path("body").asText())
                    .contains("단기 판단:")
                    .doesNotContain("같은 지역 target")
                    .doesNotContain("공통 시장 배경")
                    .doesNotContain("최신본으로 다시 교체")
                    .doesNotContain("AI API 자동 갱신")
                    .doesNotContain("투자자는");
            assertThat(OUTLOOK_WORDS.stream().anyMatch(report.path("body").asText()::contains)).isTrue();
            assertThat(report.path("expectationPoints")).hasSizeBetween(1, 2);
            assertThat(report.path("concernPoints")).hasSizeBetween(1, 2);
            assertNounLikePointStyle(report.path("expectationPoints"));
            assertNounLikePointStyle(report.path("concernPoints"));
        }
    }

    private void assertNounLikePointStyle(JsonNode points) {
        for (JsonNode point : points) {
            String text = point.asText();
            assertThat(text).isNotBlank();
            assertThat(text.length()).isLessThanOrEqualTo(34);
            for (String forbidden : FORBIDDEN_POINT_WORDS) {
                assertThat(text).doesNotContain(forbidden);
            }
        }
    }

    private void assertPointJsonUsesNounLikeStyle(String pointJson) {
        assertThat(pointJson).isNotBlank();
        for (String forbidden : FORBIDDEN_POINT_WORDS) {
            assertThat(pointJson).doesNotContain(forbidden);
        }
    }

    @Test
    @Order(6)
    void deepReportCoversEverySidoAndSigunguRegionRow() {
        Integer regionCount = jdbcTemplate.queryForObject(
                """
                select count(*)
                from real_estate_regions
                where region_level in ('sido', 'sigungu')
                  and source like 'seed:%'
                """,
                Integer.class
        );
        Integer reportCount = jdbcTemplate.queryForObject(
                """
                select count(*)
                from real_estate_regional_reports report
                join real_estate_regions region on region.target_id = report.target_id
                where region.region_level in ('sido', 'sigungu')
                  and region.source like 'seed:%'
                """,
                Integer.class
        );
        Integer deepReportCount = jdbcTemplate.queryForObject(
                """
                select count(*)
                from real_estate_regional_reports report
                join real_estate_regions region on region.target_id = report.target_id
                where report.data_quality = 'deep_researched'
                  and region.region_level in ('sido', 'sigungu')
                  and region.source like 'seed:%'
                """,
                Integer.class
        );

        assertThat(reportCount).isEqualTo(regionCount);
        assertThat(deepReportCount).isEqualTo(regionCount);

        List<Map<String, Object>> reports = jdbcTemplate.queryForList(
                """
                select report.body, report.expectation_points_json, report.concern_points_json
                from real_estate_regional_reports report
                join real_estate_regions region on region.target_id = report.target_id
                where region.region_level in ('sido', 'sigungu')
                  and region.source like 'seed:%'
                """
        );
        assertThat(reports).hasSize(regionCount);
        for (Map<String, Object> report : reports) {
            assertThat((String) report.get("body")).contains("단기 판단:");
            assertPointJsonUsesNounLikeStyle((String) report.get("expectation_points_json"));
            assertPointJsonUsesNounLikeStyle((String) report.get("concern_points_json"));
        }
    }

    @Test
    @Order(7)
    void upsertsOneLatestReportPerTargetForFutureAiAutomation() throws Exception {
        Map<String, Object> firstRequest = Map.of(
                "reports",
                List.of(Map.ofEntries(
                        Map.entry("reportId", "regional-report-region-seoul-jongno-ai-20260624"),
                        Map.entry("targetId", "region-seoul-jongno"),
                        Map.entry("reportVersion", "regional-report-v1"),
                        Map.entry("promptVersion", "regional-report-prompt-v1"),
                        Map.entry("modelName", "gpt-5-mini"),
                        Map.entry("generatedBy", "ai-api"),
                        Map.entry("title", "서울 종로구 최신 지역 리포트"),
                        Map.entry("headline", "정책·관광·업무 수요가 겹치는 도심 관찰 구간"),
                        Map.entry("summary", "종로구는 도심 업무·관광 수요와 정비 정책 변수를 함께 봐야 하는 지역입니다."),
                        Map.entry("body", "종로구는 단기 가격 방향보다 도심 수요와 정비 정책의 결합을 확인해야 합니다.\n실거래와 전세 지표가 같은 방향으로 움직이는지 분리해서 봅니다."),
                        Map.entry("expectationPoints", List.of(
                                "도심 업무 수요와 교통 접근성은 하방을 줄이는 관찰 근거입니다.",
                                "정비사업 후보지는 정책 일정이 붙으면 설명력이 커집니다."
                        )),
                        Map.entry("concernPoints", List.of(
                                "관광·상권 이슈는 주거 수요와 바로 같지 않습니다.",
                                "정비사업 기대가 가격 판단으로 과장될 수 있습니다."
                        )),
                        Map.entry("dataQuality", "partial"),
                        Map.entry("confidence", 0.71),
                        Map.entry("asOf", "2026-06-24T00:00:00Z"),
                        Map.entry("publishedAt", "2026-06-24T00:10:00Z"),
                        Map.entry("sources", List.of(Map.of(
                                "reportSourceId", "regional-report-source-jongno-policy-1",
                                "refType", "external",
                                "refId", "molit-policy-source",
                                "label", "정책 근거",
                                "title", "국토교통부 정책 발표 후보",
                                "url", "https://www.molit.go.kr/",
                                "sourceName", "국토교통부",
                                "publishedAt", "2026-06-20T00:00:00Z",
                                "dataStatus", "candidate"
                        )))
                ))
        );
        Map<String, Object> secondRequest = Map.of(
                "reports",
                List.of(Map.ofEntries(
                        Map.entry("reportId", "regional-report-region-seoul-jongno-ai-20260625"),
                        Map.entry("targetId", "region-seoul-jongno"),
                        Map.entry("reportVersion", "regional-report-v1"),
                        Map.entry("generatedBy", "ai-api"),
                        Map.entry("title", "서울 종로구 최신 지역 리포트 갱신"),
                        Map.entry("headline", "도심 수요는 유지되지만 근거 승인이 먼저입니다."),
                        Map.entry("summary", "갱신된 종로구 리포트는 최신 근거만 유지합니다."),
                        Map.entry("body", "두 번째 적재가 같은 target의 최신 리포트를 대체합니다."),
                        Map.entry("expectationPoints", List.of("업무·교통 수요는 계속 확인할 근거입니다.")),
                        Map.entry("concernPoints", List.of("승인 전 뉴스 후보를 결론처럼 쓰지 않습니다.")),
                        Map.entry("dataQuality", "partial"),
                        Map.entry("confidence", 0.63),
                        Map.entry("asOf", "2026-06-25T00:00:00Z"),
                        Map.entry("publishedAt", "2026-06-25T00:10:00Z"),
                        Map.entry("sources", List.of())
                ))
        );

        ResponseEntity<String> firstUpsert = restTemplate.postForEntity(
                "/internal/realestate/regional-reports",
                firstRequest,
                String.class
        );
        ResponseEntity<String> secondUpsert = restTemplate.postForEntity(
                "/internal/realestate/regional-reports",
                secondRequest,
                String.class
        );
        ResponseEntity<String> latest = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/regional-report",
                String.class,
                "region-seoul-jongno"
        );

        assertThat(firstUpsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode firstRoot = objectMapper.readTree(firstUpsert.getBody());
        assertThat(firstRoot.path("acceptedReports").asInt()).isEqualTo(1);
        assertThat(firstRoot.path("acceptedSources").asInt()).isEqualTo(1);

        assertThat(secondUpsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode secondRoot = objectMapper.readTree(secondUpsert.getBody());
        assertThat(secondRoot.path("acceptedReports").asInt()).isEqualTo(1);
        assertThat(secondRoot.path("acceptedSources").asInt()).isEqualTo(0);

        assertThat(latest.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode latestRoot = objectMapper.readTree(latest.getBody());
        assertThat(latestRoot.path("reportId").asText()).isEqualTo("regional-report-region-seoul-jongno-ai-20260625");
        assertThat(latestRoot.path("headline").asText()).contains("근거 승인이 먼저");
        assertThat(latestRoot.path("body").asText()).contains("최신 리포트를 대체");
        assertThat(latestRoot.path("sources")).isEmpty();
        assertThat(latestRoot.path("confidence").asDouble()).isEqualTo(0.63);
    }
}
