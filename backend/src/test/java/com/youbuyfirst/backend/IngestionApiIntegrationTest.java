package com.youbuyfirst.backend;

import com.youbuyfirst.backend.crawl.CrawlRunStatus;
import com.youbuyfirst.backend.ingestion.dto.CrawlRunReportRequest;
import com.youbuyfirst.backend.ingestion.dto.IngestionRequest;
import com.youbuyfirst.backend.ingestion.dto.IngestionResponse;
import com.youbuyfirst.backend.ingestion.dto.MentionPayload;
import com.youbuyfirst.backend.ingestion.dto.PostPayload;
import com.youbuyfirst.backend.ingestion.dto.SentimentPayload;
import com.youbuyfirst.backend.sentiment.SentimentLabel;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;

import java.time.Instant;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class IngestionApiIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private JdbcTemplate jdbcTemplate;

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

    @Test
    void recordsSkippedCrawlRunsForAdminInspection() {
        Instant backoffUntil = Instant.parse("2026-05-15T06:00:00Z");
        CrawlRunReportRequest request = new CrawlRunReportRequest(
                "NAVER",
                "naver-skip-20260515",
                Instant.parse("2026-05-15T00:00:00Z"),
                Instant.parse("2026-05-15T00:00:01Z"),
                CrawlRunStatus.SKIPPED,
                0,
                0,
                "sourceStatus=local-research-only; runtimeEnvironment=public; reason=policy denied",
                "NAVER:KR:005930",
                "stock-board",
                "policy-denied",
                backoffUntil,
                "public runtime policy denied",
                "policy denied"
        );

        ResponseEntity<Void> response = restTemplate.postForEntity(
                "/internal/ingestions/crawl-runs",
                request,
                Void.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        String runs = restTemplate.getForObject("/admin/crawl-runs?limit=5", String.class);
        assertThat(runs).contains("\"status\":\"SKIPPED\"");
        assertThat(runs).contains("sourceStatus=local-research-only");
        assertThat(runs).contains("\"targetId\":\"NAVER:KR:005930\"");
        assertThat(runs).contains("\"targetKind\":\"stock-board\"");
        assertThat(runs).contains("\"backoffCategory\":\"policy-denied\"");
        assertThat(runs).contains("\"backoffUntil\":\"2026-05-15T06:00:00Z\"");
        assertThat(runs).contains("\"skipReason\":\"policy denied\"");
    }

    @Test
    void exposesCrawlTargetsForAdminInspection() {
        String targets = restTemplate.getForObject("/admin/crawl-targets", String.class);

        assertThat(targets).contains("\"targetId\":\"NAVER:KR:005930\"");
        assertThat(targets).contains("\"status\":\"ACTIVE\"");
        assertThat(targets).contains("\"targetKind\":\"stock-board\"");
    }

    @Test
    void exposesQuoteSnapshotsWithFrontendContractAndStaleState() {
        Instant freshAsOf = Instant.now().minusSeconds(60);
        Instant staleAsOf = Instant.now().minusSeconds(60L * 60L * 48L);

        ResponseEntity<Void> upsert = restTemplate.postForEntity(
                "/internal/market/quote-snapshots",
                Map.of("items", List.of(
                        Map.ofEntries(
                                Map.entry("symbol", "AAPL"),
                                Map.entry("name", "Apple"),
                                Map.entry("market", "US"),
                                Map.entry("currency", "USD"),
                                Map.entry("price", "198.12"),
                                Map.entry("change", "1.25"),
                                Map.entry("changePct", "0.64"),
                                Map.entry("volume", 42123456),
                                Map.entry("asOf", freshAsOf.toString()),
                                Map.entry("provider", "yfinance"),
                                Map.entry("delayLabel", "Provider-delayed snapshot"),
                                Map.entry("dataStatus", "OK")
                        ),
                        Map.ofEntries(
                                Map.entry("symbol", "005930.KS"),
                                Map.entry("name", "Samsung Electronics"),
                                Map.entry("market", "KR"),
                                Map.entry("currency", "KRW"),
                                Map.entry("price", "78200"),
                                Map.entry("change", "600"),
                                Map.entry("changePct", "0.77"),
                                Map.entry("volume", 18400000),
                                Map.entry("asOf", staleAsOf.toString()),
                                Map.entry("provider", "yfinance+FinanceDataReader"),
                                Map.entry("delayLabel", "Provider-delayed snapshot"),
                                Map.entry("dataStatus", "OK")
                        )
                )),
                Void.class
        );

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/quotes?symbols=AAPL,005930.KS",
                String.class
        );

        assertThat(upsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody())
                .contains("\"symbol\":\"AAPL\"")
                .contains("\"name\":\"Apple\"")
                .contains("\"market\":\"US\"")
                .contains("\"currency\":\"USD\"")
                .contains("\"price\":198.12")
                .contains("\"change\":1.25")
                .contains("\"changePct\":0.64")
                .contains("\"volume\":42123456")
                .contains("\"provider\":\"yfinance\"")
                .contains("\"delayLabel\":\"Provider-delayed snapshot\"")
                .contains("\"stale\":false")
                .contains("\"dataStatus\":\"OK\"")
                .contains("\"symbol\":\"005930.KS\"")
                .contains("\"provider\":\"yfinance+FinanceDataReader\"")
                .contains("\"stale\":true")
                .contains("\"dataStatus\":\"STALE\"");
    }

    @Test
    void claimsOnlyDueActiveTargetsFromAllowedSources() {
        resetCrawlTargets();

        ResponseEntity<String> response = restTemplate.postForEntity(
                "/internal/crawl-targets/claim",
                Map.of(
                        "workerId", "test-worker",
                        "runtimeEnvironment", "local",
                        "allowedSources", List.of("NAVER"),
                        "limit", 10
                ),
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).contains("\"targetId\":\"NAVER:KR:005930\"");
        assertThat(response.getBody()).doesNotContain("FMKOREA:community-board");
    }

    @Test
    void claimedTargetIsNotClaimedAgainBeforeLeaseExpires() {
        resetCrawlTargets();
        Map<String, Object> request = Map.of(
                "workerId", "test-worker",
                "runtimeEnvironment", "local",
                "allowedSources", List.of("NAVER"),
                "limit", 1
        );

        ResponseEntity<String> first = restTemplate.postForEntity("/internal/crawl-targets/claim", request, String.class);
        ResponseEntity<String> second = restTemplate.postForEntity("/internal/crawl-targets/claim", request, String.class);

        assertThat(first.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(first.getBody()).contains("\"targetId\":\"NAVER:KR:005930\"");
        assertThat(second.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(second.getBody()).contains("\"targets\":[]");
    }

    @Test
    void successfulCompletionClearsBackoffAndSchedulesNormalInterval() {
        resetCrawlTargets();
        claimNaverTarget();

        ResponseEntity<Void> response = restTemplate.postForEntity(
                "/internal/crawl-targets/NAVER:KR:005930/complete",
                Map.of(
                        "workerId", "test-worker",
                        "status", "SUCCESS",
                        "startedAt", "2026-05-15T00:00:00Z",
                        "finishedAt", "2026-05-15T00:00:12Z",
                        "postsSeen", 3,
                        "postsAccepted", 2
                ),
                Void.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        String targets = restTemplate.getForObject("/admin/crawl-targets?limit=10", String.class);
        assertThat(targets).contains("\"targetId\":\"NAVER:KR:005930\"");
        assertThat(targets).contains("\"lastStatus\":\"SUCCESS\"");
        assertThat(targets).contains("\"consecutiveFailures\":0");
        assertThat(targets).contains("\"backoffCategory\":null");
    }

    @Test
    void blockedCompletionPersistsBackoffUntil() {
        resetCrawlTargets();
        claimNaverTarget();

        ResponseEntity<Void> response = restTemplate.postForEntity(
                "/internal/crawl-targets/NAVER:KR:005930/complete",
                Map.of(
                        "workerId", "test-worker",
                        "status", "PARTIAL_FAILURE",
                        "startedAt", "2026-05-15T00:00:00Z",
                        "finishedAt", "2026-05-15T00:00:12Z",
                        "postsSeen", 0,
                        "postsAccepted", 0,
                        "backoffCategory", "blocked",
                        "backoffUntil", "2026-05-15T06:00:00Z",
                        "backoffReason", "block or rate-limit"
                ),
                Void.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);

        String targets = restTemplate.getForObject("/admin/crawl-targets?limit=10", String.class);
        assertThat(targets).contains("\"targetId\":\"NAVER:KR:005930\"");
        assertThat(targets).contains("\"lastStatus\":\"PARTIAL_FAILURE\"");
        assertThat(targets).contains("\"consecutiveFailures\":1");
        assertThat(targets).contains("\"backoffCategory\":\"blocked\"");
        assertThat(targets).contains("\"backoffReason\":\"block or rate-limit\"");
    }

    private void claimNaverTarget() {
        restTemplate.postForEntity(
                "/internal/crawl-targets/claim",
                Map.of(
                        "workerId", "test-worker",
                        "runtimeEnvironment", "local",
                        "allowedSources", List.of("NAVER"),
                        "limit", 1
                ),
                String.class
        );
    }

    private void resetCrawlTargets() {
        jdbcTemplate.update("""
                update crawl_targets
                set status = 'ACTIVE',
                    next_attempt_at = timestamp '2026-05-15 00:00:00',
                    last_attempt_at = null,
                    last_success_at = null,
                    last_status = null,
                    consecutive_failures = 0,
                    backoff_category = null,
                    backoff_until = null,
                    backoff_reason = null,
                    lease_owner = null,
                    leased_until = null,
                    updated_at = current_timestamp(6)
                """);
    }
}
