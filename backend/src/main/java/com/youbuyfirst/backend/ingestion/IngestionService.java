package com.youbuyfirst.backend.ingestion;

import com.youbuyfirst.backend.common.Hashing;
import com.youbuyfirst.backend.crawl.CrawlRun;
import com.youbuyfirst.backend.crawl.CrawlRunRepository;
import com.youbuyfirst.backend.crawl.CrawlRunStatus;
import com.youbuyfirst.backend.ingestion.dto.AliasCandidatePayload;
import com.youbuyfirst.backend.ingestion.dto.CommentCollectionTargetPayload;
import com.youbuyfirst.backend.ingestion.dto.DiffusionPayload;
import com.youbuyfirst.backend.ingestion.dto.IngestionRequest;
import com.youbuyfirst.backend.ingestion.dto.IngestionResponse;
import com.youbuyfirst.backend.ingestion.dto.CrawlRunReportRequest;
import com.youbuyfirst.backend.ingestion.dto.MentionPayload;
import com.youbuyfirst.backend.ingestion.dto.PostPayload;
import com.youbuyfirst.backend.ingestion.dto.SentimentPayload;
import com.youbuyfirst.backend.instrument.Instrument;
import com.youbuyfirst.backend.instrument.InstrumentAliasCandidate;
import com.youbuyfirst.backend.instrument.InstrumentAliasCandidateRepository;
import com.youbuyfirst.backend.instrument.InstrumentRepository;
import com.youbuyfirst.backend.metrics.MetricSnapshotService;
import com.youbuyfirst.backend.post.CommunityCommentCollectionTarget;
import com.youbuyfirst.backend.post.CommunityCommentCollectionTargetRepository;
import com.youbuyfirst.backend.post.CommunityPost;
import com.youbuyfirst.backend.post.CommunityPostDiffusionEvent;
import com.youbuyfirst.backend.post.CommunityPostDiffusionEventRepository;
import com.youbuyfirst.backend.post.CommunityPostRepository;
import com.youbuyfirst.backend.post.PostMention;
import com.youbuyfirst.backend.post.PostMentionRepository;
import com.youbuyfirst.backend.sentiment.SentimentAnalysis;
import com.youbuyfirst.backend.sentiment.SentimentAnalysisRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

@Service
public class IngestionService {

    private final CommunityPostRepository postRepository;
    private final CommunityPostDiffusionEventRepository diffusionEventRepository;
    private final CommunityCommentCollectionTargetRepository commentCollectionTargetRepository;
    private final PostMentionRepository mentionRepository;
    private final SentimentAnalysisRepository sentimentRepository;
    private final InstrumentRepository instrumentRepository;
    private final InstrumentAliasCandidateRepository aliasCandidateRepository;
    private final CrawlRunRepository crawlRunRepository;
    private final MetricSnapshotService metricSnapshotService;

    public IngestionService(
            CommunityPostRepository postRepository,
            CommunityPostDiffusionEventRepository diffusionEventRepository,
            CommunityCommentCollectionTargetRepository commentCollectionTargetRepository,
            PostMentionRepository mentionRepository,
            SentimentAnalysisRepository sentimentRepository,
            InstrumentRepository instrumentRepository,
            InstrumentAliasCandidateRepository aliasCandidateRepository,
            CrawlRunRepository crawlRunRepository,
            MetricSnapshotService metricSnapshotService
    ) {
        this.postRepository = postRepository;
        this.diffusionEventRepository = diffusionEventRepository;
        this.commentCollectionTargetRepository = commentCollectionTargetRepository;
        this.mentionRepository = mentionRepository;
        this.sentimentRepository = sentimentRepository;
        this.instrumentRepository = instrumentRepository;
        this.aliasCandidateRepository = aliasCandidateRepository;
        this.crawlRunRepository = crawlRunRepository;
        this.metricSnapshotService = metricSnapshotService;
    }

    @Transactional
    public IngestionResponse ingest(IngestionRequest request) {
        int accepted = 0;
        int duplicates = 0;
        List<Instant> acceptedPublishedTimes = new ArrayList<>();
        String source = normalize(request.source());

        for (PostPayload payload : request.posts()) {
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
                    trimTo(payload.boardId(), 120),
                    payload.viewCount(),
                    payload.recommendCount(),
                    payload.commentCount(),
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

        saveDiffusionEvents(source, request.runId(), request.diffusionEvents());
        saveAliasCandidates(source, request.aliasCandidates());
        saveCommentCollectionTargets(source, request.runId(), request.commentCollectionTargets());

        crawlRunRepository.save(new CrawlRun(
                source,
                request.runId().trim(),
                request.batchStartedAt(),
                request.batchFinishedAt(),
                CrawlRunStatus.SUCCESS,
                request.posts().size(),
                accepted,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                request.pagesFetched(),
                request.rowsSeen(),
                request.ignoredPinnedCount(),
                request.duplicateStop(),
                request.cutoffStop(),
                request.oldestSeenAt(),
                request.newestSeenAt(),
                trimTo(request.lastCursor(), 120),
                trimTo(request.coverageStatus(), 40)
        ));

        metricSnapshotService.rebuildWindowsTouchedBy(acceptedPublishedTimes);
        return new IngestionResponse(source, request.runId(), request.posts().size(), accepted, duplicates);
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
                trimTo(request.errorMessage(), 1000),
                trimTo(request.targetId(), 160),
                trimTo(request.targetKind(), 40),
                trimTo(request.backoffCategory(), 40),
                request.backoffUntil(),
                trimTo(request.backoffReason(), 500),
                trimTo(request.skipReason(), 500),
                request.pagesFetched(),
                request.rowsSeen(),
                request.ignoredPinnedCount(),
                request.duplicateStop(),
                request.cutoffStop(),
                request.oldestSeenAt(),
                request.newestSeenAt(),
                trimTo(request.lastCursor(), 120),
                trimTo(request.coverageStatus(), 40)
        ));
    }

    private void saveMentions(CommunityPost post, List<MentionPayload> mentions) {
        if (mentions == null || mentions.isEmpty()) {
            return;
        }
        List<PostMention> entities = mentions.stream()
                .map(mention -> new PostMention(
                        post,
                        resolveInstrument(mention.instrumentId(), mention.market(), mention.symbol()),
                        trimTo(mention.matchedText(), 200)
                ))
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
                        resolveInstrument(sentiment.instrumentId(), sentiment.market(), sentiment.symbol()),
                        sentiment.sentiment(),
                        sentiment.confidence(),
                        trimTo(sentiment.rationale(), 500),
                        trimTo(sentiment.model(), 100),
                        Instant.now()
                ))
                .toList();
        sentimentRepository.saveAll(entities);
    }

    private void saveDiffusionEvents(String source, String runId, List<DiffusionPayload> diffusionEvents) {
        if (diffusionEvents == null || diffusionEvents.isEmpty()) {
            return;
        }
        Instant createdAt = Instant.now();
        for (DiffusionPayload payload : diffusionEvents) {
            String externalId = payload.externalId().trim();
            String diffusionType = normalizeLower(payload.diffusionType());
            if (diffusionEventRepository.existsBySourceAndExternalIdAndDiffusionTypeAndObservedAt(
                    source,
                    externalId,
                    diffusionType,
                    payload.observedAt()
            )) {
                continue;
            }
            CommunityPost linkedPost = postRepository.findBySourceAndExternalId(source, externalId).orElse(null);
            String boardId = trimTo(payload.boardId(), 120);
            if (boardId == null && linkedPost != null) {
                boardId = linkedPost.getBoardId();
            }
            diffusionEventRepository.save(new CommunityPostDiffusionEvent(
                    linkedPost,
                    source,
                    externalId,
                    boardId,
                    diffusionType,
                    payload.listPosition(),
                    payload.observedAt(),
                    payload.viewCount(),
                    payload.recommendCount(),
                    payload.commentCount(),
                    Boolean.TRUE.equals(payload.diffusionOnly()),
                    trimTo(runId, 160),
                    createdAt
            ));
        }
    }

    private void saveAliasCandidates(String source, List<AliasCandidatePayload> aliasCandidates) {
        if (aliasCandidates == null || aliasCandidates.isEmpty()) {
            return;
        }
        Instant now = Instant.now();
        for (AliasCandidatePayload payload : aliasCandidates) {
            String alias = trimTo(payload.alias(), 200);
            String normalizedAlias = normalizeAlias(alias);
            String suggestedMarket = trimTo(normalize(payload.suggestedMarket()), 20);
            String suggestedSymbol = trimTo(normalize(payload.suggestedSymbol()), 40);
            String reason = trimTo(normalizeLower(payload.reason()), 80);
            String contextSnippet = trimTo(payload.contextSnippet(), 500);
            String sampleUrl = trimTo(payload.sampleUrl(), 1000);
            aliasCandidateRepository.findBySourceAndNormalizedAliasAndSuggestedMarketAndSuggestedSymbol(
                    source,
                    normalizedAlias,
                    suggestedMarket,
                    suggestedSymbol
            ).ifPresentOrElse(existing -> {
                existing.recordSeen(reason, contextSnippet, sampleUrl, payload.observedAt(), now);
                aliasCandidateRepository.save(existing);
            }, () -> aliasCandidateRepository.save(new InstrumentAliasCandidate(
                    source,
                    alias,
                    normalizedAlias,
                    suggestedMarket,
                    suggestedSymbol,
                    reason,
                    contextSnippet,
                    sampleUrl,
                    payload.observedAt(),
                    now
            )));
        }
    }

    private void saveCommentCollectionTargets(String source, String runId, List<CommentCollectionTargetPayload> targets) {
        if (targets == null || targets.isEmpty()) {
            return;
        }
        Instant now = Instant.now();
        for (CommentCollectionTargetPayload payload : targets) {
            String externalId = payload.externalId().trim();
            CommunityPost linkedPost = postRepository.findBySourceAndExternalId(source, externalId).orElse(null);
            String resolvedBoardId = trimTo(payload.boardId(), 120);
            if (resolvedBoardId == null && linkedPost != null) {
                resolvedBoardId = linkedPost.getBoardId();
            }
            String boardId = resolvedBoardId;
            String triggerReason = normalizeLower(payload.triggerReason());
            Integer maxComments = payload.maxComments() == null ? 30 : payload.maxComments();
            Integer priority = payload.priority() == null ? 100 : payload.priority();
            String crawlRunId = trimTo(runId, 160);
            commentCollectionTargetRepository.findBySourceAndExternalId(source, externalId).ifPresentOrElse(existing -> {
                existing.refreshFrom(
                        linkedPost,
                        boardId,
                        triggerReason,
                        payload.triggeredAt(),
                        maxComments,
                        priority,
                        payload.viewCount(),
                        payload.recommendCount(),
                        payload.commentCount(),
                        crawlRunId,
                        now
                );
                commentCollectionTargetRepository.save(existing);
            }, () -> commentCollectionTargetRepository.save(new CommunityCommentCollectionTarget(
                    linkedPost,
                    source,
                    externalId,
                    boardId,
                    triggerReason,
                    payload.triggeredAt(),
                    maxComments,
                    priority,
                    payload.viewCount(),
                    payload.recommendCount(),
                    payload.commentCount(),
                    "PENDING",
                    crawlRunId,
                    now,
                    now
            )));
        }
    }

    private Instrument getOrCreateInstrument(String market, String symbol) {
        String normalizedMarket = normalize(market);
        String normalizedSymbol = normalize(symbol);
        return instrumentRepository.findByMarketIgnoreCaseAndSymbolIgnoreCase(normalizedMarket, normalizedSymbol)
                .orElseGet(() -> instrumentRepository.save(new Instrument(normalizedMarket, normalizedSymbol, normalizedSymbol, normalizedSymbol, "UNKNOWN")));
    }

    private Instrument resolveInstrument(Long instrumentId, String market, String symbol) {
        if (instrumentId != null) {
            return instrumentRepository.findById(instrumentId)
                    .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "unknown instrumentId"));
        }
        return getOrCreateInstrument(market, symbol);
    }

    private static String normalize(String value) {
        return value == null ? "" : value.trim().toUpperCase();
    }

    private static String normalizeAlias(String value) {
        return value == null ? "" : value.trim().toUpperCase(Locale.ROOT);
    }

    private static String normalizeLower(String value) {
        return value == null ? "" : value.trim().toLowerCase();
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
