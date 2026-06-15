package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateContentBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateContentItemRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateContentItemResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateContentTargetRequest;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Locale;

@Service
public class RealEstateContentService {

    private static final String CONTENT_SOURCE_REF = "content";

    private final RealEstateContentItemRepository itemRepository;
    private final RealEstateContentTargetLinkRepository linkRepository;
    private final RealEstateTargetRepository targetRepository;
    private final RealEstateTimelineService timelineService;

    public RealEstateContentService(
            RealEstateContentItemRepository itemRepository,
            RealEstateContentTargetLinkRepository linkRepository,
            RealEstateTargetRepository targetRepository,
            RealEstateTimelineService timelineService
    ) {
        this.itemRepository = itemRepository;
        this.linkRepository = linkRepository;
        this.targetRepository = targetRepository;
        this.timelineService = timelineService;
    }

    @Transactional
    public RealEstateContentBatchResponse upsertAll(Collection<RealEstateContentItemRequest> requests) {
        Instant now = Instant.now();
        int acceptedItems = 0;
        int acceptedTargetLinks = 0;
        int materializedTimelineEvents = 0;
        for (RealEstateContentItemRequest request : requests) {
            String contentId = requireText(request.contentId(), "contentId");
            RealEstateContentItem item = itemRepository.findById(contentId)
                    .or(() -> itemRepository.findByUrl(requireText(request.url(), "url")))
                    .orElseGet(() -> new RealEstateContentItem(contentId, now));
            item.update(
                    trimToNull(request.sourceId()),
                    normalizeLower(request.contentType()),
                    requireText(request.title(), "title"),
                    trimTo(request.snippet(), 1000),
                    requireText(request.url(), "url"),
                    trimToNull(request.domain()),
                    request.publishedAt(),
                    trimToNull(request.metricLabel()),
                    trimToNull(request.statusLabel()),
                    request.ingestedAt(),
                    normalizeLower(request.dataStatus()),
                    now
            );
            itemRepository.save(item);
            acceptedItems++;

            for (RealEstateContentTargetRequest targetRequest : request.targets()) {
                RealEstateTarget target = targetRepository.findById(requireText(targetRequest.targetId(), "targetId"))
                        .orElseThrow(() -> new ResponseStatusException(
                                HttpStatus.BAD_REQUEST,
                                "unknown real-estate target: " + targetRequest.targetId()
                        ));
                String linkType = normalizeLower(requireText(targetRequest.linkType(), "linkType"));
                String reviewState = normalizeLower(defaultIfBlank(targetRequest.reviewState(), "candidate"));
                RealEstateContentTargetLinkId linkId = new RealEstateContentTargetLinkId(
                        item.getId(),
                        target.getId(),
                        linkType
                );
                RealEstateContentTargetLink link = linkRepository.findById(linkId)
                        .orElseGet(() -> new RealEstateContentTargetLink(item, target, linkType, now));
                link.update(clampConfidence(targetRequest.confidence()), reviewState, now);
                linkRepository.save(link);
                acceptedTargetLinks++;

                if ("approved".equals(reviewState)) {
                    timelineService.upsertSourceTimeline(
                            target.getId(),
                            item.getContentType(),
                            CONTENT_SOURCE_REF,
                            item.getId(),
                            item.getTitle(),
                            item.getSnippet(),
                            item.getPublishedAt() == null ? item.getIngestedAt() : item.getPublishedAt(),
                            item.getIngestedAt(),
                            item.getDataStatus(),
                            now
                    );
                    materializedTimelineEvents++;
                } else {
                    timelineService.deleteSourceTimeline(target.getId(), CONTENT_SOURCE_REF, item.getId());
                }
            }
        }
        return new RealEstateContentBatchResponse(acceptedItems, acceptedTargetLinks, materializedTimelineEvents);
    }

    @Transactional(readOnly = true)
    public List<RealEstateContentItemResponse> listForTarget(String targetId, String feed, int limit) {
        int boundedLimit = Math.max(1, Math.min(limit, 100));
        targetRepository.findById(targetId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "unknown real-estate target: " + targetId
                ));
        return linkRepository.findApprovedByTarget(
                targetId,
                feedType(feed),
                PageRequest.of(0, boundedLimit)
        ).stream().map(this::toLinkedResponse).toList();
    }

    @Transactional(readOnly = true)
    public List<RealEstateContentItemResponse> listInternalForTarget(
            String targetId,
            String feed,
            int limit,
            String reviewState,
            String linkType
    ) {
        int boundedLimit = Math.max(1, Math.min(limit, 100));
        targetRepository.findById(targetId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "unknown real-estate target: " + targetId
                ));
        return linkRepository.findInternalByTarget(
                targetId,
                feedType(feed),
                filterType(reviewState),
                filterType(linkType),
                PageRequest.of(0, boundedLimit)
        ).stream().map(this::toLinkedResponse).toList();
    }

    @Transactional(readOnly = true)
    public List<RealEstateContentItemResponse> listNewsroom(String feed, int page, int pageSize) {
        int boundedPage = Math.max(0, page - 1);
        int boundedPageSize = Math.max(1, Math.min(pageSize, 100));
        return itemRepository.searchNewsroom(
                feedType(feed),
                PageRequest.of(boundedPage, boundedPageSize)
        ).stream().map(this::toUnlinkedResponse).toList();
    }

    private RealEstateContentItemResponse toLinkedResponse(RealEstateContentTargetLink link) {
        RealEstateContentItem item = link.getContentItem();
        return new RealEstateContentItemResponse(
                item.getId(),
                item.getSourceId(),
                item.getContentType(),
                item.getTitle(),
                item.getSnippet(),
                item.getUrl(),
                item.getDomain(),
                item.getPublishedAt(),
                item.getMetricLabel(),
                item.getStatusLabel(),
                item.getIngestedAt(),
                item.getDataStatus(),
                link.getTargetId(),
                link.getLinkType(),
                round(link.getConfidence(), 2),
                link.getReviewState()
        );
    }

    private RealEstateContentItemResponse toUnlinkedResponse(RealEstateContentItem item) {
        return new RealEstateContentItemResponse(
                item.getId(),
                item.getSourceId(),
                item.getContentType(),
                item.getTitle(),
                item.getSnippet(),
                item.getUrl(),
                item.getDomain(),
                item.getPublishedAt(),
                item.getMetricLabel(),
                item.getStatusLabel(),
                item.getIngestedAt(),
                item.getDataStatus(),
                null,
                null,
                null,
                null
        );
    }

    private static String feedType(String feed) {
        String normalized = trimToNull(feed);
        if (normalized == null || "all".equalsIgnoreCase(normalized)) {
            return null;
        }
        return normalizeLower(normalized);
    }

    private static String filterType(String value) {
        String normalized = trimToNull(value);
        if (normalized == null || "all".equalsIgnoreCase(normalized)) {
            return null;
        }
        return normalizeLower(normalized);
    }

    private static String requireText(String value, String fieldName) {
        String trimmed = trimToNull(value);
        if (trimmed == null) {
            throw new IllegalArgumentException(fieldName + " is required");
        }
        return trimmed;
    }

    private static String defaultIfBlank(String value, String fallback) {
        String trimmed = trimToNull(value);
        return trimmed == null ? fallback : trimmed;
    }

    private static String trimTo(String value, int maxLength) {
        String trimmed = trimToNull(value);
        if (trimmed == null || trimmed.length() <= maxLength) {
            return trimmed;
        }
        return trimmed.substring(0, maxLength);
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static String normalizeLower(String value) {
        return value.trim().toLowerCase(Locale.ROOT);
    }

    private static Double clampConfidence(Double value) {
        if (value == null) {
            return 0.5;
        }
        return Math.max(0.0, Math.min(1.0, value));
    }

    private static double round(double value, int places) {
        double factor = Math.pow(10, places);
        return Math.round(value * factor) / factor;
    }
}
