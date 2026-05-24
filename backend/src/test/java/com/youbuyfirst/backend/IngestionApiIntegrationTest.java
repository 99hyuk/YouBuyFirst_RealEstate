package com.youbuyfirst.backend;

import com.youbuyfirst.backend.market.ChartCandleRefreshRequest;
import com.youbuyfirst.backend.market.ChartCandleRefreshRequestRepository;
import com.youbuyfirst.backend.crawl.CrawlRunStatus;
import com.youbuyfirst.backend.ingestion.dto.CrawlRunReportRequest;
import com.youbuyfirst.backend.ingestion.dto.DiffusionPayload;
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
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import jakarta.persistence.LockModeType;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.Collection;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class IngestionApiIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private ChartCandleRefreshRequestRepository chartCandleRefreshRequestRepository;

    @Autowired
    private PlatformTransactionManager transactionManager;

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
                        "stock",
                        1200,
                        3,
                        7,
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

        String posts = restTemplate.getForObject("/admin/posts?source=FMKOREA&limit=5", String.class);
        assertThat(posts)
                .contains("\"boardId\":\"stock\"")
                .contains("\"viewCount\":1200")
                .contains("\"recommendCount\":3")
                .contains("\"commentCount\":7");

        ResponseEntity<String> watermark = restTemplate.getForEntity(
                "/internal/crawl-watermarks?source=FMKOREA&boardId=stock",
                String.class
        );
        assertThat(watermark.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(watermark.getBody())
                .contains("\"source\":\"FMKOREA\"")
                .contains("\"boardId\":\"stock\"")
                .contains("\"lastSeenExternalId\":\"fmk-1\"")
                .contains("\"lastSeenPublishedAt\":\"2026-05-13T00:05:00Z\"");
    }

    @Test
    void recordsDiffusionEventsSeparatelyFromPostDeduplication() {
        IngestionRequest request = new IngestionRequest(
                "DCINSIDE",
                "dc-us-popular-20260524-1000",
                Instant.parse("2026-05-24T01:00:00Z"),
                Instant.parse("2026-05-24T01:02:00Z"),
                List.of(new PostPayload(
                        "dc-us-777",
                        "https://gall.dcinside.com/mgallery/board/view/?id=stockus&no=777",
                        "NVDA concept thread",
                        "NVDA earnings talk is spreading on the board.",
                        "dc-user",
                        Instant.parse("2026-05-24T00:58:00Z"),
                        "stockus",
                        2300,
                        41,
                        86,
                        List.of(new MentionPayload("US", "NVDA", "NVDA")),
                        List.of(new SentimentPayload("US", "NVDA", SentimentLabel.BULLISH, 0.72, "earnings expectation mentioned", "mock"))
                )),
                List.of(new DiffusionPayload(
                        "dc-us-777",
                        "stockus",
                        "concept",
                        1,
                        Instant.parse("2026-05-24T01:01:00Z"),
                        2300,
                        41,
                        86,
                        false
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
        assertThat(duplicate.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(duplicate.getBody()).isNotNull();
        assertThat(duplicate.getBody().duplicatePosts()).isEqualTo(1);

        String events = restTemplate.getForObject("/admin/diffusion-events?source=DCINSIDE&limit=5", String.class);
        assertThat(events)
                .contains("\"source\":\"DCINSIDE\"")
                .contains("\"boardId\":\"stockus\"")
                .contains("\"externalId\":\"dc-us-777\"")
                .contains("\"diffusionType\":\"concept\"")
                .contains("\"listPosition\":1")
                .contains("\"viewCount\":2300")
                .contains("\"recommendCount\":41")
                .contains("\"commentCount\":86")
                .contains("\"diffusionOnly\":false")
                .contains("\"crawlRunId\":\"dc-us-popular-20260524-1000\"");
        Integer eventCount = jdbcTemplate.queryForObject(
                "select count(*) from community_post_diffusion_events where source = ? and external_id = ?",
                Integer.class,
                "DCINSIDE",
                "dc-us-777"
        );
        assertThat(eventCount).isEqualTo(1);
    }

    @Test
    void recordsAliasCandidatesWithoutCreatingConfirmedMentions() {
        Map<String, Object> request = Map.ofEntries(
                Map.entry("source", "DCINSIDE"),
                Map.entry("runId", "dc-us-alias-20260525-1000"),
                Map.entry("batchStartedAt", "2026-05-25T01:00:00Z"),
                Map.entry("batchFinishedAt", "2026-05-25T01:02:00Z"),
                Map.entry("posts", List.of()),
                Map.entry("aliasCandidates", List.of(Map.ofEntries(
                        Map.entry("alias", "슬라"),
                        Map.entry("suggestedMarket", "US"),
                        Map.entry("suggestedSymbol", "TSLA"),
                        Map.entry("reason", "review-alias"),
                        Map.entry("contextSnippet", "슬라 실적 기대감 때문에 오늘 게시판에서 계속 언급됨"),
                        Map.entry("sampleUrl", "https://gall.dcinside.com/mgallery/board/view/?id=stockus&no=888"),
                        Map.entry("observedAt", "2026-05-25T01:00:00Z")
                )))
        );

        ResponseEntity<IngestionResponse> first = restTemplate.postForEntity(
                "/internal/ingestions/community-posts",
                request,
                IngestionResponse.class
        );
        ResponseEntity<IngestionResponse> second = restTemplate.postForEntity(
                "/internal/ingestions/community-posts",
                request,
                IngestionResponse.class
        );

        assertThat(first.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(second.getStatusCode()).isEqualTo(HttpStatus.OK);

        String candidates = restTemplate.getForObject("/admin/alias-candidates?source=DCINSIDE&limit=5", String.class);
        assertThat(candidates)
                .contains("\"source\":\"DCINSIDE\"")
                .contains("\"alias\":\"슬라\"")
                .contains("\"normalizedAlias\":\"슬라\"")
                .contains("\"suggestedMarket\":\"US\"")
                .contains("\"suggestedSymbol\":\"TSLA\"")
                .contains("\"reason\":\"review-alias\"")
                .contains("\"status\":\"PENDING\"")
                .contains("\"occurrenceCount\":2");
        Integer candidateCount = jdbcTemplate.queryForObject(
                "select count(*) from instrument_alias_candidates where source = ? and normalized_alias = ?",
                Integer.class,
                "DCINSIDE",
                "슬라"
        );
        assertThat(candidateCount).isEqualTo(1);
        Integer mentionCount = jdbcTemplate.queryForObject(
                "select count(*) from post_mentions pm join instruments i on i.id = pm.instrument_id where i.market = ? and i.symbol = ?",
                Integer.class,
                "US",
                "TSLA"
        );
        assertThat(mentionCount).isEqualTo(0);

        String aliases = restTemplate.getForObject("/admin/instrument-aliases?market=US&limit=20", String.class);
        assertThat(aliases)
                .contains("\"symbol\":\"TSLA\"")
                .contains("\"alias\":\"TSLA\"")
                .contains("\"status\":\"ACCEPTED\"")
                .contains("\"confidence\":1.0");
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
                "policy denied",
                2,
                43,
                1,
                true,
                false,
                Instant.parse("2026-05-15T00:00:00Z"),
                Instant.parse("2026-05-15T00:29:00Z"),
                "2",
                "complete"
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
        assertThat(runs).contains("\"pagesFetched\":2");
        assertThat(runs).contains("\"rowsSeen\":43");
        assertThat(runs).contains("\"ignoredPinnedCount\":1");
        assertThat(runs).contains("\"duplicateStop\":true");
        assertThat(runs).contains("\"cutoffStop\":false");
        assertThat(runs).contains("\"lastCursor\":\"2\"");
        assertThat(runs).contains("\"coverageStatus\":\"complete\"");
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
    void exposesChartCandlesWithDisplayOnlyContract() {
        Instant asOf = Instant.now().minusSeconds(60);

        ResponseEntity<Void> upsert = restTemplate.postForEntity(
                "/internal/market/chart-candles",
                Map.of("items", List.of(
                        Map.ofEntries(
                                Map.entry("symbol", "005930.KS"),
                                Map.entry("name", "Samsung Electronics"),
                                Map.entry("market", "KR"),
                                Map.entry("currency", "KRW"),
                                Map.entry("range", "3M"),
                                Map.entry("interval", "1d"),
                                Map.entry("provider", "yfinance+FinanceDataReader"),
                                Map.entry("delayLabel", "Yahoo Finance delayed up to 30 min"),
                                Map.entry("asOf", asOf.toString()),
                                Map.entry("dataStatus", "OK"),
                                Map.entry("bars", List.of(
                                        Map.of(
                                                "date", "2026-05-20",
                                                "open", "280000",
                                                "high", "301000",
                                                "low", "279000",
                                                "close", "295500",
                                                "volume", 24688716
                                        ),
                                        Map.of(
                                                "date", "2026-05-21",
                                                "open", "295500",
                                                "high", "302000",
                                                "low", "292000",
                                                "close", "297750",
                                                "volume", 22059084
                                        )
                                ))
                        )
                )),
                Void.class
        );

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/market/chart-candles?symbol=005930.KS&range=3M&interval=1d",
                String.class
        );

        assertThat(upsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody())
                .contains("\"symbol\":\"005930.KS\"")
                .contains("\"name\":\"Samsung Electronics\"")
                .contains("\"market\":\"KR\"")
                .contains("\"currency\":\"KRW\"")
                .contains("\"range\":\"3M\"")
                .contains("\"interval\":\"1d\"")
                .contains("\"provider\":\"yfinance+FinanceDataReader\"")
                .contains("\"delayLabel\":\"Yahoo Finance delayed up to 30 min\"")
                .contains("\"stale\":false")
                .contains("\"dataStatus\":\"OK\"")
                .contains("\"date\":\"2026-05-20\"")
                .contains("\"open\":280000")
                .contains("\"high\":301000")
                .contains("\"low\":279000")
                .contains("\"close\":295500")
                .contains("\"volume\":24688716")
                .contains("\"displayOnly\":true")
                .contains("\"rawMinute\":false")
                .contains("\"downloadable\":false")
                .contains("\"maxBars\":66")
                .doesNotContain("individual")
                .doesNotContain("foreign")
                .doesNotContain("institution");
    }

    @Test
    void queuesChartCandleRefreshWhenCacheIsMissingInsteadOfCallingYahooFromBackend() {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/market/chart-candles?symbol=NASDAQ:MSFT&range=1M&interval=1d",
                String.class
        );
        ResponseEntity<String> claim = restTemplate.postForEntity(
                "/internal/market/chart-candle-refresh-requests/claim",
                Map.of("limit", 10),
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(claim.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody())
                .contains("\"symbol\":\"MSFT\"")
                .contains("\"name\":\"Microsoft\"")
                .contains("\"market\":\"US\"")
                .contains("\"currency\":\"USD\"")
                .contains("\"provider\":\"yfinance\"")
                .contains("\"delayLabel\":\"Yahoo Finance 10 min refresh snapshot\"")
                .contains("\"stale\":true")
                .contains("\"dataStatus\":\"INSUFFICIENT\"")
                .contains("\"bars\":[]")
                .contains("\"maxBars\":22");
        assertThat(claim.getBody())
                .contains("\"symbol\":\"MSFT\"")
                .contains("\"range\":\"1M\"")
                .contains("\"interval\":\"1d\"");
    }

    @Test
    void returnsStaleChartCandlesAndQueuesPipelineRefreshWhenCacheIsStale() {
        Instant staleAsOf = Instant.now().minusSeconds(60L * 60L * 72L);

        ResponseEntity<Void> staleUpsert = restTemplate.postForEntity(
                "/internal/market/chart-candles",
                Map.of("items", List.of(
                        Map.ofEntries(
                                Map.entry("symbol", "TSLA"),
                                Map.entry("name", "Tesla"),
                                Map.entry("market", "US"),
                                Map.entry("currency", "USD"),
                                Map.entry("range", "3M"),
                                Map.entry("interval", "1d"),
                                Map.entry("provider", "yfinance"),
                                Map.entry("delayLabel", "Yahoo Finance 10 min refresh snapshot"),
                                Map.entry("asOf", staleAsOf.toString()),
                                Map.entry("dataStatus", "OK"),
                                Map.entry("bars", List.of(
                                        Map.of(
                                                "date", "2026-05-01",
                                                "open", "160.00",
                                                "high", "164.00",
                                                "low", "158.00",
                                                "close", "161.00",
                                                "volume", 80100000
                                        )
                                ))
                        )
                )),
                Void.class
        );

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/market/chart-candles?symbol=TSLA&range=3M&interval=1d",
                String.class
        );
        ResponseEntity<String> claim = restTemplate.postForEntity(
                "/internal/market/chart-candle-refresh-requests/claim",
                Map.of("limit", 10),
                String.class
        );

        assertThat(staleUpsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(claim.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody())
                .contains("\"symbol\":\"TSLA\"")
                .contains("\"name\":\"Tesla\"")
                .contains("\"stale\":true")
                .contains("\"dataStatus\":\"STALE\"")
                .contains("\"date\":\"2026-05-01\"")
                .contains("\"close\":161.00");
        assertThat(claim.getBody())
                .contains("\"symbol\":\"TSLA\"")
                .contains("\"range\":\"3M\"")
                .contains("\"interval\":\"1d\"");
    }

    @Test
    void reclaimsTimedOutChartCandleRefreshRequests() {
        jdbcTemplate.update("delete from chart_candle_refresh_requests");
        jdbcTemplate.update(
                """
                insert into chart_candle_refresh_requests
                    (symbol, range_label, candle_interval, status, requested_at, last_attempt_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                "JPM",
                "1M",
                "1d",
                ChartCandleRefreshRequest.STATUS_IN_PROGRESS,
                Timestamp.from(Instant.parse("2026-05-24T00:00:00Z")),
                Timestamp.from(Instant.now().minusSeconds(60L * 10L))
        );

        ResponseEntity<String> claim = restTemplate.postForEntity(
                "/internal/market/chart-candle-refresh-requests/claim",
                Map.of("limit", 10),
                String.class
        );

        assertThat(claim.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(claim.getBody())
                .contains("\"symbol\":\"JPM\"")
                .contains("\"range\":\"1M\"")
                .contains("\"interval\":\"1d\"");
    }

    @Test
    void locksPendingChartCandleRefreshRequestsSoConcurrentClaimersCannotReadTheSameRow() throws Exception {
        jdbcTemplate.update("delete from chart_candle_refresh_requests");
        jdbcTemplate.update(
                """
                insert into chart_candle_refresh_requests
                    (symbol, range_label, candle_interval, status, requested_at)
                values (?, ?, ?, ?, ?)
                """,
                "LOCKTEST",
                "1M",
                "1d",
                ChartCandleRefreshRequest.STATUS_PENDING,
                Timestamp.from(Instant.parse("2026-05-24T00:00:00Z"))
        );

        CountDownLatch firstTransactionSelected = new CountDownLatch(1);
        ExecutorService executor = Executors.newFixedThreadPool(2);
        TransactionTemplate transactionTemplate = new TransactionTemplate(transactionManager);

        try {
            Future<List<String>> firstWorker = executor.submit(() -> transactionTemplate.execute(status -> {
                List<ChartCandleRefreshRequest> requests = chartCandleRefreshRequestRepository.findClaimable(
                        Set.of(ChartCandleRefreshRequest.STATUS_PENDING),
                        PageRequest.of(0, 1)
                );
                firstTransactionSelected.countDown();
                sleep(300);
                requests.forEach(request -> request.claim(Instant.now()));
                return requests.stream().map(ChartCandleRefreshRequest::getSymbol).toList();
            }));

            assertThat(firstTransactionSelected.await(10, TimeUnit.SECONDS)).isTrue();

            Future<List<String>> secondWorker = executor.submit(() -> transactionTemplate.execute(status ->
                    chartCandleRefreshRequestRepository.findClaimable(
                                    Set.of(ChartCandleRefreshRequest.STATUS_PENDING),
                                    PageRequest.of(0, 1)
                            )
                            .stream()
                            .map(ChartCandleRefreshRequest::getSymbol)
                            .toList()
            ));

            assertThat(firstWorker.get(10, TimeUnit.SECONDS)).containsExactly("LOCKTEST");
            assertThat(secondWorker.get(10, TimeUnit.SECONDS)).doesNotContain("LOCKTEST");
        } finally {
            executor.shutdownNow();
        }
    }

    @Test
    void claimableChartCandleRefreshRequestsAreSelectedWithDatabaseWriteLocks() throws Exception {
        Lock lock = ChartCandleRefreshRequestRepository.class
                .getMethod("findClaimable", Collection.class, Pageable.class)
                .getAnnotation(Lock.class);

        assertThat(lock).isNotNull();
        assertThat(lock.value()).isEqualTo(LockModeType.PESSIMISTIC_WRITE);
    }

    @Test
    void exposesBackendDerivedTechnicalIndicatorsFromCachedChartCandles() {
        Instant asOf = Instant.now().minusSeconds(60);

        ResponseEntity<Void> upsert = restTemplate.postForEntity(
                "/internal/market/chart-candles",
                Map.of("items", List.of(
                        Map.ofEntries(
                                Map.entry("symbol", "005930.KS"),
                                Map.entry("name", "Samsung Electronics"),
                                Map.entry("market", "KR"),
                                Map.entry("currency", "KRW"),
                                Map.entry("range", "3M"),
                                Map.entry("interval", "1d"),
                                Map.entry("provider", "yfinance+FinanceDataReader"),
                                Map.entry("delayLabel", "Yahoo Finance delayed up to 30 min"),
                                Map.entry("asOf", asOf.toString()),
                                Map.entry("dataStatus", "OK"),
                                Map.entry("bars", indicatorBars())
                        )
                )),
                Void.class
        );

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/market/technical-indicators?symbol=005930.KS&range=3M&interval=1d&rsiPeriod=14&bollingerPeriod=20&bollingerMultiplier=2",
                String.class
        );

        assertThat(upsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody())
                .contains("\"symbol\":\"005930.KS\"")
                .contains("\"provider\":\"backend-derived\"")
                .contains("\"sourceProvider\":\"yfinance+FinanceDataReader\"")
                .contains("\"delayLabel\":\"Yahoo Finance delayed up to 30 min\"")
                .contains("\"dataStatus\":\"OK\"")
                .contains("\"rsi\":{\"period\":14")
                .contains("\"date\":\"2026-05-15\",\"value\":100.00")
                .contains("\"bollingerBands\":{\"period\":20,\"multiplier\":2.00")
                .contains("\"date\":\"2026-05-20\",\"upper\":22.03,\"middle\":10.50,\"lower\":-1.03");
    }

    @Test
    void replacesExistingChartCandlesWhenCorrectedDatesOverlap() {
        Instant asOf = Instant.now().minusSeconds(60);

        ResponseEntity<Void> firstUpsert = restTemplate.postForEntity(
                "/internal/market/chart-candles",
                Map.of("items", List.of(
                        chartCandleSet(
                                "000660.KS",
                                "5Y",
                                asOf,
                                List.of(
                                        chartCandleBar("2026-05-14", "190000", 1000),
                                        chartCandleBar("2026-05-15", "191000", 2000)
                                )
                        )
                )),
                Void.class
        );

        ResponseEntity<Void> secondUpsert = restTemplate.postForEntity(
                "/internal/market/chart-candles",
                Map.of("items", List.of(
                        chartCandleSet(
                                "000660.KS",
                                "5Y",
                                asOf.plusSeconds(60),
                                List.of(
                                        chartCandleBar("2026-05-15", "270500", 38075487),
                                        chartCandleBar("2026-05-18", "281000", 33555214)
                                )
                        )
                )),
                Void.class
        );

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/market/chart-candles?symbol=000660.KS&range=5Y&interval=1d",
                String.class
        );

        assertThat(firstUpsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(secondUpsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody())
                .contains("\"date\":\"2026-05-15\"")
                .contains("\"close\":270500")
                .contains("\"volume\":38075487")
                .contains("\"date\":\"2026-05-18\"")
                .contains("\"close\":281000")
                .contains("\"volume\":33555214")
                .doesNotContain("\"date\":\"2026-05-14\"");
    }

    @Test
    void rejectsUnsupportedChartCandleInterval() {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/market/chart-candles?symbol=005930.KS&range=3M&interval=5m",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
    }

    @Test
    void exposesInvestorFlowHistoryAsLatestFirstDomesticSliceAndSkipsErrorRows() {
        Instant asOf = Instant.now().minusSeconds(60);

        ResponseEntity<Void> upsert = restTemplate.postForEntity(
                "/internal/market/investor-flows",
                Map.of("items", List.of(
                        Map.ofEntries(
                                Map.entry("symbol", "005930.KS"),
                                Map.entry("name", "Samsung Electronics"),
                                Map.entry("market", "KR"),
                                Map.entry("currency", "KRW"),
                                Map.entry("tradeDate", "2026-05-22"),
                                Map.entry("asOf", asOf.toString()),
                                Map.entry("provider", "pykrx"),
                                Map.entry("sourceLabel", "KRX investor trading by date via pykrx"),
                                Map.entry("delayLabel", "Previous trading day investor flow"),
                                Map.entry("dataStatus", "PROVIDER_ERROR"),
                                Map.entry("individual", Map.of(
                                        "netAmount", "0",
                                        "netVolume", 0
                                )),
                                Map.entry("foreign", Map.of(
                                        "netAmount", "0",
                                        "netVolume", 0
                                )),
                                Map.entry("institution", Map.of(
                                        "netAmount", "0",
                                        "netVolume", 0
                                ))
                        ),
                        Map.ofEntries(
                                Map.entry("symbol", "005930.KS"),
                                Map.entry("name", "Samsung Electronics"),
                                Map.entry("market", "KR"),
                                Map.entry("currency", "KRW"),
                                Map.entry("tradeDate", "2026-05-19"),
                                Map.entry("asOf", asOf.minusSeconds(172800).toString()),
                                Map.entry("provider", "naver-finance"),
                                Map.entry("sourceLabel", "Naver Finance investor trend; individual is residual from foreign and institution"),
                                Map.entry("delayLabel", "Previous trading day investor trend"),
                                Map.entry("dataStatus", "OK"),
                                Map.entry("individual", investorLeg(null, -6280909, true)),
                                Map.entry("foreign", investorLeg(null, 3672423, false)),
                                Map.entry("institution", investorLeg(null, 2608486, false))
                        ),
                        Map.ofEntries(
                                Map.entry("symbol", "005930.KS"),
                                Map.entry("name", "Samsung Electronics"),
                                Map.entry("market", "KR"),
                                Map.entry("currency", "KRW"),
                                Map.entry("tradeDate", "2026-05-21"),
                                Map.entry("asOf", asOf.toString()),
                                Map.entry("provider", "pykrx"),
                                Map.entry("sourceLabel", "KRX investor trading by date via pykrx"),
                                Map.entry("delayLabel", "Previous trading day investor flow"),
                                Map.entry("dataStatus", "OK"),
                                Map.entry("individual", Map.of(
                                        "netAmount", "125000000000",
                                        "netVolume", 1700000
                                )),
                                Map.entry("foreign", Map.of(
                                        "netAmount", "-90000000000",
                                        "netVolume", -1100000
                                )),
                                Map.entry("institution", Map.of(
                                        "netAmount", "-35000000000",
                                        "netVolume", -600000
                                ))
                        ),
                        Map.ofEntries(
                                Map.entry("symbol", "005930.KS"),
                                Map.entry("name", "Samsung Electronics"),
                                Map.entry("market", "KR"),
                                Map.entry("currency", "KRW"),
                                Map.entry("tradeDate", "2026-05-20"),
                                Map.entry("asOf", asOf.minusSeconds(86400).toString()),
                                Map.entry("provider", "pykrx"),
                                Map.entry("sourceLabel", "KRX investor trading by date via pykrx"),
                                Map.entry("delayLabel", "Previous trading day investor flow"),
                                Map.entry("dataStatus", "OK"),
                                Map.entry("individual", Map.of(
                                        "netAmount", "-12000000000",
                                        "netVolume", -120000
                                )),
                                Map.entry("foreign", Map.of(
                                        "netAmount", "8000000000",
                                        "netVolume", 90000
                                )),
                                Map.entry("institution", Map.of(
                                        "netAmount", "4000000000",
                                        "netVolume", 30000
                                ))
                        )
                )),
                Void.class
        );

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/market/investor-flows/history?symbol=005930.KS&limit=20",
                String.class
        );

        assertThat(upsert.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody())
                .contains("\"symbol\":\"005930.KS\"")
                .contains("\"name\":\"Samsung Electronics\"")
                .contains("\"market\":\"KR\"")
                .contains("\"currency\":\"KRW\"")
                .contains("\"tradeDate\":\"2026-05-21\"")
                .contains("\"provider\":\"pykrx\"")
                .contains("\"sourceLabel\":\"KRX investor trading by date via pykrx\"")
                .contains("\"delayLabel\":\"Previous trading day investor flow\"")
                .contains("\"stale\":false")
                .contains("\"dataStatus\":\"OK\"")
                .contains("\"individual\":{\"netAmount\":125000000000.00,\"netVolume\":1700000,\"derived\":false}")
                .contains("\"foreign\":{\"netAmount\":-90000000000.00,\"netVolume\":-1100000,\"derived\":false}")
                .contains("\"institution\":{\"netAmount\":-35000000000.00,\"netVolume\":-600000,\"derived\":false}")
                .contains("\"tradeDate\":\"2026-05-20\"")
                .contains("\"tradeDate\":\"2026-05-19\"")
                .contains("\"provider\":\"naver-finance\"")
                .contains("\"sourceLabel\":\"Naver Finance investor trend; individual is residual from foreign and institution\"")
                .contains("\"delayLabel\":\"Previous trading day investor trend\"")
                .contains("\"individual\":{\"netAmount\":null,\"netVolume\":-6280909,\"derived\":true}")
                .contains("\"foreign\":{\"netAmount\":null,\"netVolume\":3672423,\"derived\":false}")
                .contains("\"institution\":{\"netAmount\":null,\"netVolume\":2608486,\"derived\":false}")
                .doesNotContain("\"tradeDate\":\"2026-05-22\"")
                .doesNotContain("\"dataStatus\":\"PROVIDER_ERROR\"")
                .doesNotContain("\"bars\"")
                .doesNotContain("\"price\"");
        assertThat(response.getBody().indexOf("\"tradeDate\":\"2026-05-21\""))
                .isLessThan(response.getBody().indexOf("\"tradeDate\":\"2026-05-20\""));
    }

    @Test
    void removesSingleInvestorFlowPublicEndpoint() {
        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/market/investor-flows?symbols=000660.KS",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
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

    private static Map<String, Object> investorLeg(Object netAmount, long netVolume, boolean derived) {
        Map<String, Object> leg = new LinkedHashMap<>();
        leg.put("netAmount", netAmount);
        leg.put("netVolume", netVolume);
        leg.put("derived", derived);
        return leg;
    }

    private static Map<String, Object> chartCandleSet(
            String symbol,
            String range,
            Instant asOf,
            List<Map<String, Object>> bars
    ) {
        return Map.ofEntries(
                Map.entry("symbol", symbol),
                Map.entry("name", "SK hynix"),
                Map.entry("market", "KR"),
                Map.entry("currency", "KRW"),
                Map.entry("range", range),
                Map.entry("interval", "1d"),
                Map.entry("provider", "yfinance+FinanceDataReader"),
                Map.entry("delayLabel", "Yahoo Finance delayed up to 30 min"),
                Map.entry("asOf", asOf.toString()),
                Map.entry("dataStatus", "OK"),
                Map.entry("bars", bars)
        );
    }

    private static Map<String, Object> chartCandleBar(String date, String close, long volume) {
        return Map.of(
                "date", date,
                "open", close,
                "high", close,
                "low", close,
                "close", close,
                "volume", volume
        );
    }

    private static List<Map<String, Object>> indicatorBars() {
        return java.util.stream.IntStream.rangeClosed(1, 20)
                .mapToObj(day -> {
                    String close = Integer.toString(day);
                    return chartCandleBar(
                            LocalDate.of(2026, 5, day).toString(),
                            close,
                            1000L + day
                    );
                })
                .toList();
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

    private static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(exception);
        }
    }
}
