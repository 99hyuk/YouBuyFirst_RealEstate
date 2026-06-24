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
        ResponseEntity<String> evidenceContent = restTemplate.getForEntity(
                "/internal/realestate/targets/{targetId}/content?feed=news&limit=10&reviewState=candidate&linkType=context",
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

        assertThat(evidenceContent.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode evidenceContentItems = objectMapper.readTree(evidenceContent.getBody()).path("items");
        assertThat(evidenceContentItems).hasSize(1);
        assertThat(evidenceContentItems.get(0).path("contentId").asText()).isEqualTo("content-news-20260612-jongno");
        assertThat(evidenceContentItems.get(0).path("targetId").asText()).isEqualTo("region-seoul");
        assertThat(evidenceContentItems.get(0).path("reviewState").asText()).isEqualTo("candidate");
        assertThat(evidenceContentItems.get(0).path("linkType").asText()).isEqualTo("context");
    }

    @Test
    void newsroomPrioritizesCuratedContentAheadOfSearchCandidates() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("contentId", "content-news-candidate-newer"),
                                Map.entry("sourceId", "serpapi:google_news"),
                                Map.entry("contentType", "news"),
                                Map.entry("title", "검색 후보 최신 기사"),
                                Map.entry("snippet", "검색 후보로 들어온 최신 기사입니다."),
                                Map.entry("url", "https://example.com/news/candidate-newer"),
                                Map.entry("domain", "example.com"),
                                Map.entry("publishedAt", "2026-06-18T04:00:00Z"),
                                Map.entry("metricLabel", "query: 서울 부동산"),
                                Map.entry("statusLabel", "search_candidate"),
                                Map.entry("ingestedAt", "2026-06-18T04:10:00Z"),
                                Map.entry("dataStatus", "candidate"),
                                Map.entry("targets", List.of())
                        ),
                        Map.ofEntries(
                                Map.entry("contentId", "content-news-curated-older"),
                                Map.entry("sourceId", "manual_curated:news"),
                                Map.entry("contentType", "news"),
                                Map.entry("title", "검증 큐레이션 기사"),
                                Map.entry("snippet", "검증된 수동 큐레이션 기사입니다."),
                                Map.entry("url", "https://example.com/news/curated-older"),
                                Map.entry("domain", "example.com"),
                                Map.entry("publishedAt", "2026-06-01T04:00:00Z"),
                                Map.entry("metricLabel", "큐레이션"),
                                Map.entry("statusLabel", "수동 큐레이션"),
                                Map.entry("ingestedAt", "2026-06-18T04:20:00Z"),
                                Map.entry("dataStatus", "curated"),
                                Map.entry("targets", List.of())
                        )
                )
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/content-items",
                request,
                String.class
        );
        ResponseEntity<String> newsroom = restTemplate.getForEntity(
                "/api/realestate/newsroom?feed=news&page=1&pageSize=100",
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(newsroom.getStatusCode()).isEqualTo(HttpStatus.OK);

        JsonNode items = objectMapper.readTree(newsroom.getBody()).path("items");
        int curatedIndex = indexOfContent(items, "content-news-curated-older");
        int candidateIndex = indexOfContent(items, "content-news-candidate-newer");

        assertThat(curatedIndex).isGreaterThanOrEqualTo(0);
        assertThat(candidateIndex).isGreaterThanOrEqualTo(0);
        assertThat(curatedIndex).isLessThan(candidateIndex);
    }

    @Test
    void newsroomAcceptsUiPluralFeedAliases() throws Exception {
        Map<String, Object> request = Map.of(
                "items",
                List.of(
                        Map.ofEntries(
                                Map.entry("contentId", "content-report-ui-alias"),
                                Map.entry("sourceId", "manual_curated:report"),
                                Map.entry("contentType", "report"),
                                Map.entry("title", "KB housing market report"),
                                Map.entry("snippet", "Curated monthly report"),
                                Map.entry("url", "https://example.com/reports/kb-202606"),
                                Map.entry("domain", "www.kbfg.com"),
                                Map.entry("publishedAt", "2026-06-16T00:00:00Z"),
                                Map.entry("metricLabel", "monthly report"),
                                Map.entry("statusLabel", "curated"),
                                Map.entry("ingestedAt", "2026-06-16T01:00:00Z"),
                                Map.entry("dataStatus", "curated"),
                                Map.entry("targets", List.of())
                        ),
                        Map.ofEntries(
                                Map.entry("contentId", "content-video-ui-alias"),
                                Map.entry("sourceId", "manual_curated:youtube"),
                                Map.entry("contentType", "video"),
                                Map.entry("title", "Housing market video"),
                                Map.entry("snippet", "Curated video"),
                                Map.entry("url", "https://www.youtube.com/watch?v=demo202606"),
                                Map.entry("domain", "www.youtube.com"),
                                Map.entry("publishedAt", "2026-06-15T00:00:00Z"),
                                Map.entry("metricLabel", "video"),
                                Map.entry("statusLabel", "curated"),
                                Map.entry("ingestedAt", "2026-06-15T01:00:00Z"),
                                Map.entry("dataStatus", "curated"),
                                Map.entry("targets", List.of())
                        ),
                        Map.ofEntries(
                                Map.entry("contentId", "content-link-ui-alias"),
                                Map.entry("sourceId", "manual_curated:blog"),
                                Map.entry("contentType", "link"),
                                Map.entry("title", "Housing market blog"),
                                Map.entry("snippet", "Curated blog link"),
                                Map.entry("url", "https://brunch.co.kr/@demo/1"),
                                Map.entry("domain", "brunch.co.kr"),
                                Map.entry("publishedAt", "2026-06-14T00:00:00Z"),
                                Map.entry("metricLabel", "blog"),
                                Map.entry("statusLabel", "curated"),
                                Map.entry("ingestedAt", "2026-06-14T01:00:00Z"),
                                Map.entry("dataStatus", "curated"),
                                Map.entry("targets", List.of())
                        )
                )
        );

        ResponseEntity<String> ingest = restTemplate.postForEntity(
                "/internal/realestate/content-items",
                request,
                String.class
        );

        assertThat(ingest.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(contentIdsForFeed("reports")).contains("content-report-ui-alias");
        assertThat(contentIdsForFeed("videos")).contains("content-video-ui-alias");
        assertThat(contentIdsForFeed("links")).contains("content-link-ui-alias");
    }

    private static int indexOfContent(JsonNode items, String contentId) {
        for (int index = 0; index < items.size(); index++) {
            if (contentId.equals(items.get(index).path("contentId").asText())) {
                return index;
            }
        }
        return -1;
    }

    private List<String> contentIdsForFeed(String feed) throws Exception {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/newsroom?feed={feed}&page=1&pageSize=100",
                String.class,
                feed
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(response.getBody()).path("items");
        return items.findValuesAsText("contentId");
    }
}
