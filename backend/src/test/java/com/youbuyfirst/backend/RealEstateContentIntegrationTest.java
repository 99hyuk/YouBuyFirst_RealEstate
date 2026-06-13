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
class RealEstateContentIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void upsertsApprovedContentLinksAndMaterializesTargetTimeline() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(Map.ofEntries(
                        Map.entry("contentId", "content-news-20260612-jongno"),
                        Map.entry("sourceId", "ddangzipgo"),
                        Map.entry("contentType", "news"),
                        Map.entry("title", "종로 도심 정비사업 후보지 발표"),
                        Map.entry("snippet", "종로 일대 정비사업 후보지가 공개되며 지역 커뮤니티 관심이 늘었습니다."),
                        Map.entry("url", "https://example.com/news/jongno-20260612"),
                        Map.entry("domain", "example.com"),
                        Map.entry("publishedAt", "2026-06-12T04:00:00Z"),
                        Map.entry("metricLabel", "뉴스"),
                        Map.entry("statusLabel", "링크 확인"),
                        Map.entry("ingestedAt", "2026-06-12T04:10:00Z"),
                        Map.entry("dataStatus", "ok"),
                        Map.entry("targets", List.of(
                                Map.of(
                                        "targetId", "region-seoul-jongno",
                                        "linkType", "mentioned",
                                        "confidence", 0.86,
                                        "reviewState", "approved"
                                ),
                                Map.of(
                                        "targetId", "region-seoul",
                                        "linkType", "context",
                                        "confidence", 0.52,
                                        "reviewState", "candidate"
                                )
                        ))
                ))
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/content-items",
                request,
                String.class
        );
        ResponseEntity<String> targetContent = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/content?feed=news&limit=10",
                String.class,
                "region-seoul-jongno"
        );
        ResponseEntity<String> approvedTimeline = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/timeline?eventType=news&limit=10",
                String.class,
                "region-seoul-jongno"
        );
        ResponseEntity<String> candidateTimeline = restTemplate.getForEntity(
                "/api/realestate/targets/{targetId}/timeline?eventType=news&limit=10",
                String.class,
                "region-seoul"
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode ingestRoot = objectMapper.readTree(ingest.getBody());
        assertThat(ingestRoot.path("acceptedItems").asInt()).isEqualTo(1);
        assertThat(ingestRoot.path("acceptedTargetLinks").asInt()).isEqualTo(2);
        assertThat(ingestRoot.path("materializedTimelineEvents").asInt()).isEqualTo(1);

        assertThat(targetContent.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode contentItems = objectMapper.readTree(targetContent.getBody()).path("items");
        assertThat(contentItems).hasSize(1);
        JsonNode content = contentItems.get(0);
        assertThat(content.path("contentId").asText()).isEqualTo("content-news-20260612-jongno");
        assertThat(content.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(content.path("contentType").asText()).isEqualTo("news");
        assertThat(content.path("title").asText()).isEqualTo("종로 도심 정비사업 후보지 발표");
        assertThat(content.path("linkType").asText()).isEqualTo("mentioned");
        assertThat(content.path("reviewState").asText()).isEqualTo("approved");

        assertThat(approvedTimeline.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode timelineItems = objectMapper.readTree(approvedTimeline.getBody()).path("items");
        assertThat(timelineItems).hasSize(1);
        JsonNode event = timelineItems.get(0);
        assertThat(event.path("targetId").asText()).isEqualTo("region-seoul-jongno");
        assertThat(event.path("eventType").asText()).isEqualTo("news");
        assertThat(event.path("sourceRefType").asText()).isEqualTo("content");
        assertThat(event.path("sourceRefId").asText()).isEqualTo("content-news-20260612-jongno");
        assertThat(event.path("title").asText()).isEqualTo("종로 도심 정비사업 후보지 발표");
        assertThat(event.path("summary").asText()).contains("정비사업 후보지");
        assertThat(event.path("occurredAt").asText()).isEqualTo("2026-06-12T04:00:00Z");
        assertThat(event.path("asOf").asText()).isEqualTo("2026-06-12T04:10:00Z");
        assertThat(event.path("dataStatus").asText()).isEqualTo("ok");

        assertThat(candidateTimeline.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(objectMapper.readTree(candidateTimeline.getBody()).path("items")).isEmpty();
    }
}
