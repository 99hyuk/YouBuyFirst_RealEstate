package com.humanindicator.backend;

import com.humanindicator.backend.ingestion.dto.IngestionRequest;
import com.humanindicator.backend.ingestion.dto.IngestionResponse;
import com.humanindicator.backend.ingestion.dto.MentionPayload;
import com.humanindicator.backend.ingestion.dto.PostPayload;
import com.humanindicator.backend.ingestion.dto.SentimentPayload;
import com.humanindicator.backend.sentiment.SentimentLabel;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class IngestionApiIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void ingestsCommunityPostsIdempotentlyAndCreatesMetrics() {
        IngestionRequest request = new IngestionRequest(
                "FMKOREA",
                "run-20260513-0900",
                Instant.parse("2026-05-13T00:00:00Z"),
                Instant.parse("2026-05-13T00:30:00Z"),
                List.of(new PostPayload(
                        "fmk-1",
                        "https://www.fmkorea.com/stock/1",
                        "테슬라랑 엔비디아 오늘 강하다",
                        "TSLA NVDA 둘 다 실적 기대감 때문에 매수세가 붙는 듯합니다.",
                        "anonymous",
                        Instant.parse("2026-05-13T00:05:00Z"),
                        List.of(
                                new MentionPayload("US", "TSLA", "테슬라"),
                                new MentionPayload("US", "NVDA", "엔비디아")
                        ),
                        List.of(
                                new SentimentPayload("US", "TSLA", SentimentLabel.BULLISH, 0.91, "실적 기대감 언급", "mock"),
                                new SentimentPayload("US", "NVDA", SentimentLabel.BULLISH, 0.87, "매수세 언급", "mock")
                        )
                ))
        );

        ResponseEntity<IngestionResponse> first = restTemplate.postForEntity(
                "/internal/ingestions/community-posts",
                request,
                IngestionResponse.class
        );
        ResponseEntity<IngestionResponse> duplicate = restTemplate.postForEntity(
                "/internal/ingestions/community-posts",
                request,
                IngestionResponse.class
        );

        assertThat(first.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(first.getBody()).isNotNull();
        assertThat(first.getBody().acceptedPosts()).isEqualTo(1);
        assertThat(first.getBody().duplicatePosts()).isZero();
        assertThat(duplicate.getBody()).isNotNull();
        assertThat(duplicate.getBody().acceptedPosts()).isZero();
        assertThat(duplicate.getBody().duplicatePosts()).isEqualTo(1);

        String metrics = restTemplate.getForObject("/admin/stocks/TSLA/metrics?market=US", String.class);
        assertThat(metrics).contains("\"mentionCount\":1");
        assertThat(metrics).contains("\"bullishCount\":1");
        assertThat(metrics).contains("\"netSentiment\":1.0");
    }

    @Test
    void rejectsInvalidSentimentPayloads() {
        IngestionRequest request = new IngestionRequest(
                "NAVER",
                "bad-run",
                Instant.parse("2026-05-13T00:00:00Z"),
                Instant.parse("2026-05-13T00:30:00Z"),
                List.of(new PostPayload(
                        "",
                        "not-a-url",
                        "",
                        "",
                        "",
                        Instant.parse("2026-05-13T00:05:00Z"),
                        List.of(),
                        List.of()
                ))
        );

        ResponseEntity<String> response = restTemplate.postForEntity(
                "/internal/ingestions/community-posts",
                request,
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
    }
}
