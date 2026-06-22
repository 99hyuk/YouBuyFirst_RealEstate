package com.youbuyfirst.backend.ingestion;

import com.youbuyfirst.backend.common.Hashing;
import com.youbuyfirst.backend.crawl.CrawlRun;
import com.youbuyfirst.backend.crawl.CrawlRunRepository;
import com.youbuyfirst.backend.crawl.CrawlRunStatus;
import com.youbuyfirst.backend.ingestion.dto.CommentCollectionTargetPayload;
import com.youbuyfirst.backend.ingestion.dto.CommunityPostExportItemResponse;
import com.youbuyfirst.backend.ingestion.dto.CommunityPostExportResponse;
import com.youbuyfirst.backend.ingestion.dto.CrawlRunReportRequest;
import com.youbuyfirst.backend.ingestion.dto.DiffusionPayload;
import com.youbuyfirst.backend.ingestion.dto.IngestionRequest;
import com.youbuyfirst.backend.ingestion.dto.IngestionResponse;
import com.youbuyfirst.backend.ingestion.dto.PostPayload;
import com.youbuyfirst.backend.post.CommunityCommentCollectionTarget;
import com.youbuyfirst.backend.post.CommunityCommentCollectionTargetRepository;
import com.youbuyfirst.backend.post.CommunityPost;
import com.youbuyfirst.backend.post.CommunityPostDiffusionEvent;
import com.youbuyfirst.backend.post.CommunityPostDiffusionEventRepository;
import com.youbuyfirst.backend.post.CommunityPostRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.data.domain.PageRequest;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Service
public class IngestionService {

    private final CommunityPostRepository postRepository;
    private final CommunityPostDiffusionEventRepository diffusionEventRepository;
    private final CommunityCommentCollectionTargetRepository commentCollectionTargetRepository;
    private final CrawlRunRepository crawlRunRepository;

    public IngestionService(
            CommunityPostRepository postRepository,
            CommunityPostDiffusionEventRepository diffusionEventRepository,
            CommunityCommentCollectionTargetRepository commentCollectionTargetRepository,
            CrawlRunRepository crawlRunRepository
    ) {
        this.postRepository = postRepository;
        this.diffusionEventRepository = diffusionEventRepository;
        this.commentCollectionTargetRepository = commentCollectionTargetRepository;
        this.crawlRunRepository = crawlRunRepository;
    }

    @Transactional
    public IngestionResponse ingest(IngestionRequest request) {
        int accepted = 0;
        int duplicates = 0;
        String source = normalize(request.source());

        for (PostPayload payload : request.posts()) {
            String externalId = payload.externalId().trim();
            String contentSnippet = trimTo(payload.contentSnippet(), 1000);
            String boardId = trimTo(payload.boardId(), 120);
            String contentHash = Hashing.sha256(source + "|" + externalId + "|" + payload.url() + "|" + payload.title() + "|" + nullToEmpty(contentSnippet));
            Optional<CommunityPost> existing = postRepository.findBySourceAndExternalId(source, externalId);
            if (existing.isPresent()) {
                duplicates++;
                if (existing.get().enrichMissingDetails(
                        contentSnippet,
                        boardId,
                        payload.viewCount(),
                        payload.recommendCount(),
                        payload.commentCount(),
                        contentHash,
                        Instant.now()
                )) {
                    postRepository.save(existing.get());
                }
                continue;
            }

            CommunityPost post = new CommunityPost(
                    source,
                    externalId,
                    payload.url(),
                    payload.title().trim(),
                    contentSnippet,
                    boardId,
                    payload.viewCount(),
                    payload.recommendCount(),
                    payload.commentCount(),
                    Hashing.sha256(nullToEmpty(payload.authorDisplayName()).trim()),
                    payload.publishedAt(),
                    contentHash,
                    Instant.now()
            );
            postRepository.save(post);
            accepted++;
        }

        saveDiffusionEvents(source, request.runId(), request.diffusionEvents());
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

        return new IngestionResponse(source, request.runId(), request.posts().size(), accepted, duplicates);
    }

    @Transactional(readOnly = true)
    public CommunityPostExportResponse exportCommunityPosts(
            String source,
            Instant publishedFrom,
            Instant publishedTo,
            int limit,
            int page
    ) {
        int boundedLimit = Math.max(1, Math.min(limit, 5000));
        int boundedPage = Math.max(0, page);
        String normalizedSource = trimTo(source, 40) == null ? null : normalize(source);
        List<CommunityPostExportItemResponse> items = postRepository.findForReactionExport(
                        normalizedSource,
                        publishedFrom,
                        publishedTo,
                        PageRequest.of(boundedPage, boundedLimit)
                ).stream()
                .map(CommunityPostExportItemResponse::from)
                .toList();
        return new CommunityPostExportResponse(
                normalizedSource,
                publishedFrom,
                publishedTo,
                boundedLimit,
                boundedPage,
                items
        );
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

    private static String normalize(String value) {
        return value == null ? "" : value.trim().toUpperCase();
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
