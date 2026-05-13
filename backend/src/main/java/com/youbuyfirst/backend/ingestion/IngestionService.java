package com.youbuyfirst.backend.ingestion;

import com.youbuyfirst.backend.common.Hashing;
import com.youbuyfirst.backend.crawl.CrawlRun;
import com.youbuyfirst.backend.crawl.CrawlRunRepository;
import com.youbuyfirst.backend.crawl.CrawlRunStatus;
import com.youbuyfirst.backend.ingestion.dto.IngestionRequest;
import com.youbuyfirst.backend.ingestion.dto.IngestionResponse;
import com.youbuyfirst.backend.ingestion.dto.CrawlRunReportRequest;
import com.youbuyfirst.backend.ingestion.dto.MentionPayload;
import com.youbuyfirst.backend.ingestion.dto.PostPayload;
import com.youbuyfirst.backend.ingestion.dto.SentimentPayload;
import com.youbuyfirst.backend.instrument.Instrument;
import com.youbuyfirst.backend.instrument.InstrumentRepository;
import com.youbuyfirst.backend.metrics.MetricSnapshotService;
import com.youbuyfirst.backend.post.CommunityPost;
import com.youbuyfirst.backend.post.CommunityPostRepository;
import com.youbuyfirst.backend.post.PostMention;
import com.youbuyfirst.backend.post.PostMentionRepository;
import com.youbuyfirst.backend.sentiment.SentimentAnalysis;
import com.youbuyfirst.backend.sentiment.SentimentAnalysisRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Service
public class IngestionService {

    private final CommunityPostRepository postRepository;
    private final PostMentionRepository mentionRepository;
    private final SentimentAnalysisRepository sentimentRepository;
    private final InstrumentRepository instrumentRepository;
    private final CrawlRunRepository crawlRunRepository;
    private final MetricSnapshotService metricSnapshotService;

    public IngestionService(
            CommunityPostRepository postRepository,
            PostMentionRepository mentionRepository,
            SentimentAnalysisRepository sentimentRepository,
            InstrumentRepository instrumentRepository,
            CrawlRunRepository crawlRunRepository,
            MetricSnapshotService metricSnapshotService
    ) {
        this.postRepository = postRepository;
        this.mentionRepository = mentionRepository;
        this.sentimentRepository = sentimentRepository;
        this.instrumentRepository = instrumentRepository;
        this.crawlRunRepository = crawlRunRepository;
        this.metricSnapshotService = metricSnapshotService;
    }

    @Transactional
    public IngestionResponse ingest(IngestionRequest request) {
        int accepted = 0;
        int duplicates = 0;
        List<Instant> acceptedPublishedTimes = new ArrayList<>();

        for (PostPayload payload : request.posts()) {
            String source = normalize(request.source());
            String externalId = payload.externalId().trim();
            if (postRepository.existsBySourceAndExternalId(source, externalId)) {
                duplicates++;
                continue;
            }

            CommunityPost post = new CommunityPost(
                    source,
                    externalId,
                    payload.url(),
                    payload.title().trim(),
                    trimTo(payload.contentSnippet(), 1000),
                    Hashing.sha256(nullToEmpty(payload.authorDisplayName()).trim()),
                    payload.publishedAt(),
                    Hashing.sha256(source + "|" + externalId + "|" + payload.url() + "|" + payload.title() + "|" + nullToEmpty(payload.contentSnippet())),
                    Instant.now()
            );
            postRepository.save(post);

            saveMentions(post, payload.mentions());
            saveSentiments(post, payload.sentiments());
            acceptedPublishedTimes.add(payload.publishedAt());
            accepted++;
        }

        crawlRunRepository.save(new CrawlRun(
                normalize(request.source()),
                request.runId().trim(),
                request.batchStartedAt(),
                request.batchFinishedAt(),
                CrawlRunStatus.SUCCESS,
                request.posts().size(),
                accepted,
                null
        ));

        metricSnapshotService.rebuildWindowsTouchedBy(acceptedPublishedTimes);
        return new IngestionResponse(normalize(request.source()), request.runId(), request.posts().size(), accepted, duplicates);
    }

    @Transactional
    public void recordCrawlRun(CrawlRunReportRequest request) {
        crawlRunRepository.save(new CrawlRun(
                normalize(request.source()),
                request.runId().trim(),
                request.batchStartedAt(),
                request.batchFinishedAt(),
                request.status(),
                request.postsSeen(),
                request.postsAccepted(),
                trimTo(request.errorMessage(), 1000)
        ));
    }

    private void saveMentions(CommunityPost post, List<MentionPayload> mentions) {
        if (mentions == null || mentions.isEmpty()) {
            return;
        }
        List<PostMention> entities = mentions.stream()
                .map(mention -> new PostMention(post, getOrCreateInstrument(mention.market(), mention.symbol()), trimTo(mention.matchedText(), 200)))
                .toList();
        mentionRepository.saveAll(entities);
    }

    private void saveSentiments(CommunityPost post, List<SentimentPayload> sentiments) {
        if (sentiments == null || sentiments.isEmpty()) {
            return;
        }
        List<SentimentAnalysis> entities = sentiments.stream()
                .map(sentiment -> new SentimentAnalysis(
                        post,
                        getOrCreateInstrument(sentiment.market(), sentiment.symbol()),
                        sentiment.sentiment(),
                        sentiment.confidence(),
                        trimTo(sentiment.rationale(), 500),
                        trimTo(sentiment.model(), 100),
                        Instant.now()
                ))
                .toList();
        sentimentRepository.saveAll(entities);
    }

    private Instrument getOrCreateInstrument(String market, String symbol) {
        String normalizedMarket = normalize(market);
        String normalizedSymbol = normalize(symbol);
        return instrumentRepository.findByMarketIgnoreCaseAndSymbolIgnoreCase(normalizedMarket, normalizedSymbol)
                .orElseGet(() -> instrumentRepository.save(new Instrument(normalizedMarket, normalizedSymbol, normalizedSymbol, normalizedSymbol, "UNKNOWN")));
    }

    private static String normalize(String value) {
        return value == null ? "" : value.trim().toUpperCase();
    }

    private static String trimTo(String value, int maxLength) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.length() <= maxLength ? trimmed : trimmed.substring(0, maxLength);
    }

    private static String nullToEmpty(String value) {
        return value == null ? "" : value;
    }
}
