package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.realestate.dto.PolicyEventBatchResponse;
import com.youbuyfirst.backend.realestate.dto.PolicyEventRequest;
import com.youbuyfirst.backend.realestate.dto.PolicyEventTargetRequest;
import com.youbuyfirst.backend.realestate.dto.TimelineEventResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Locale;

@Service
public class RealEstateTimelineService {

    private static final String POLICY_EVENT_REF = "policy_event";
    private static final String MARKET_FACT_REF = "market_fact";

    private final PolicyEventRepository policyEventRepository;
    private final PolicyEventTargetRepository policyEventTargetRepository;
    private final TimelineEventRepository timelineEventRepository;
    private final RealEstateTargetRepository targetRepository;
    private final ObjectMapper objectMapper;

    public RealEstateTimelineService(
            PolicyEventRepository policyEventRepository,
            PolicyEventTargetRepository policyEventTargetRepository,
            TimelineEventRepository timelineEventRepository,
            RealEstateTargetRepository targetRepository,
            ObjectMapper objectMapper
    ) {
        this.policyEventRepository = policyEventRepository;
        this.policyEventTargetRepository = policyEventTargetRepository;
        this.timelineEventRepository = timelineEventRepository;
        this.targetRepository = targetRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public PolicyEventBatchResponse upsertPolicyEvents(Collection<PolicyEventRequest> requests) {
        Instant now = Instant.now();
        int acceptedEvents = 0;
        int acceptedTargetLinks = 0;
        int materializedTimelineEvents = 0;
        for (PolicyEventRequest request : requests) {
            String eventId = requireText(request.eventId(), "eventId");
            PolicyEvent event = policyEventRepository.findById(eventId)
                    .orElseGet(() -> new PolicyEvent(eventId, now));
            event.update(
                    normalizeLower(request.eventType()),
                    request.title().trim(),
                    trimToNull(request.summary()),
                    trimToNull(request.sourceUrl()),
                    request.publishedAt(),
                    request.effectiveFrom(),
                    request.effectiveTo(),
                    normalizeLower(request.targetScope()),
                    normalizeLower(request.dataStatus()),
                    now
            );
            policyEventRepository.save(event);
            acceptedEvents++;

            for (PolicyEventTargetRequest targetRequest : request.targets()) {
                String targetId = requireText(targetRequest.targetId(), "targetId");
                targetRepository.findById(targetId)
                        .orElseThrow(() -> new ResponseStatusException(
                                HttpStatus.BAD_REQUEST,
                                "unknown real-estate target: " + targetId
                        ));
                String impactType = normalizeLower(requireText(targetRequest.impactType(), "impactType"));
                String reviewState = normalizeLower(defaultIfBlank(targetRequest.reviewState(), "candidate"));
                PolicyEventTargetId linkId = new PolicyEventTargetId(eventId, targetId, impactType);
                PolicyEventTarget link = policyEventTargetRepository.findById(linkId)
                        .orElseGet(() -> new PolicyEventTarget(eventId, targetId, impactType, now));
                link.update(clampConfidence(targetRequest.confidence()), reviewState, now);
                policyEventTargetRepository.save(link);
                acceptedTargetLinks++;

                if ("approved".equals(reviewState)) {
                    upsertTimelineEvent(event, targetId, impactType, now);
                    materializedTimelineEvents++;
                } else {
                    timelineEventRepository.deleteById(timelineEventId(eventId, targetId, impactType));
                }
            }
        }
        return new PolicyEventBatchResponse(acceptedEvents, acceptedTargetLinks, materializedTimelineEvents);
    }

    @Transactional
    public void upsertMarketFactTimeline(RealEstateMarketFact fact, Instant now) {
        if (fact.getId() == null || trimToNull(fact.getTargetId()) == null) {
            return;
        }
        upsertSourceTimeline(
                fact.getTargetId(),
                MARKET_FACT_REF,
                MARKET_FACT_REF,
                String.valueOf(fact.getId()),
                marketFactTitle(fact.getFactType()),
                marketFactSummary(fact),
                toStartOfDayUtc(fact.getObservedAt()),
                toStartOfDayUtc(fact.getAsOf()),
                fact.isStale() ? "stale" : fact.getDataStatus(),
                now
        );
    }

    @Transactional
    public void upsertSourceTimeline(
            String targetId,
            String eventType,
            String sourceRefType,
            String sourceRefId,
            String title,
            String summary,
            Instant occurredAt,
            Instant asOf,
            String dataStatus,
            Instant now
    ) {
        String normalizedTargetId = requireText(targetId, "targetId");
        String normalizedSourceRefType = normalizeLower(requireText(sourceRefType, "sourceRefType"));
        String normalizedSourceRefId = requireText(sourceRefId, "sourceRefId");
        String id = sourceTimelineEventId(normalizedTargetId, normalizedSourceRefType, normalizedSourceRefId);
        TimelineEvent timelineEvent = timelineEventRepository.findById(id)
                .orElseGet(() -> new TimelineEvent(id, normalizedTargetId, now));
        timelineEvent.update(
                normalizeLower(requireText(eventType, "eventType")),
                normalizedSourceRefType,
                normalizedSourceRefId,
                requireText(title, "title"),
                trimToNull(summary),
                occurredAt,
                asOf,
                normalizeLower(defaultIfBlank(dataStatus, "unknown")),
                now
        );
        timelineEventRepository.save(timelineEvent);
    }

    @Transactional
    public void deleteSourceTimeline(String targetId, String sourceRefType, String sourceRefId) {
        String normalizedTargetId = requireText(targetId, "targetId");
        String normalizedSourceRefType = normalizeLower(requireText(sourceRefType, "sourceRefType"));
        String normalizedSourceRefId = requireText(sourceRefId, "sourceRefId");
        timelineEventRepository.deleteById(sourceTimelineEventId(
                normalizedTargetId,
                normalizedSourceRefType,
                normalizedSourceRefId
        ));
    }

    @Transactional(readOnly = true)
    public List<TimelineEventResponse> listTimeline(String targetId, String eventType, int limit) {
        targetRepository.findById(targetId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "unknown real-estate target: " + targetId
                ));
        int boundedLimit = Math.max(1, Math.min(limit, 200));
        return timelineEventRepository.searchByTarget(
                targetId,
                trimToNull(eventType) == null ? null : normalizeLower(eventType),
                PageRequest.of(0, boundedLimit)
        ).stream().map(this::toResponse).toList();
    }

    private void upsertTimelineEvent(PolicyEvent event, String targetId, String impactType, Instant now) {
        String id = timelineEventId(event.getId(), targetId, impactType);
        TimelineEvent timelineEvent = timelineEventRepository.findById(id)
                .orElseGet(() -> new TimelineEvent(id, targetId, now));
        Instant occurredAt = event.getPublishedAt() == null ? event.getEffectiveFrom() : event.getPublishedAt();
        timelineEvent.update(
                event.getEventType(),
                POLICY_EVENT_REF,
                event.getId(),
                event.getTitle(),
                event.getSummary(),
                occurredAt,
                occurredAt,
                event.getDataStatus(),
                now
        );
        timelineEventRepository.save(timelineEvent);
    }

    private TimelineEventResponse toResponse(TimelineEvent event) {
        return new TimelineEventResponse(
                event.getId(),
                event.getTargetId(),
                event.getEventType(),
                event.getSourceRefType(),
                event.getSourceRefId(),
                event.getTitle(),
                event.getSummary(),
                event.getOccurredAt(),
                event.getAsOf(),
                event.getDataStatus()
        );
    }

    private static String timelineEventId(String eventId, String targetId, String impactType) {
        return String.join(":", POLICY_EVENT_REF, eventId, targetId, impactType);
    }

    private static String sourceTimelineEventId(String targetId, String sourceRefType, String sourceRefId) {
        return String.join(":", sourceRefType, sourceRefId, targetId);
    }

    private String marketFactTitle(String factType) {
        return switch (factType) {
            case "apt_trade" -> "매매 실거래";
            case "apt_rent" -> "전월세 실거래";
            case "listing_count" -> "매물 수";
            case "price_index" -> "가격지수";
            default -> "시장 사실 데이터";
        };
    }

    private String marketFactSummary(RealEstateMarketFact fact) {
        JsonNode valueJson = readJson(fact.getValueJson());
        return switch (fact.getFactType()) {
            case "apt_trade" -> joinSummaryParts(
                    textOrNull(valueJson.path("apartmentName")),
                    formatManwonAsEok(valueJson.path("dealAmountManwon")),
                    formatArea(valueJson.path("exclusiveAreaM2")),
                    datePart("계약", fact.getObservedAt())
            );
            case "apt_rent" -> joinSummaryParts(
                    textOrNull(valueJson.path("apartmentName")),
                    "보증금 " + formatManwonAsEok(valueJson.path("depositManwon")),
                    "월세 " + valueJson.path("monthlyRentManwon").asText("확인 필요") + "만원",
                    formatArea(valueJson.path("exclusiveAreaM2")),
                    datePart("계약", fact.getObservedAt())
            );
            case "listing_count" -> joinSummaryParts(
                    "매물 " + valueJson.path("listingCount").asText("확인 필요") + "건",
                    datePart("기준", fact.getAsOf())
            );
            case "price_index" -> joinSummaryParts(
                    "지수 " + valueJson.path("indexValue").asText("확인 필요"),
                    datePart("기준", fact.getAsOf())
            );
            default -> joinSummaryParts(
                    fact.getProviderDataset(),
                    fact.getProviderObjectId(),
                    datePart("기준", fact.getAsOf())
            );
        };
    }

    private JsonNode readJson(String value) {
        try {
            return objectMapper.readTree(value);
        } catch (JsonProcessingException exc) {
            throw new IllegalStateException("invalid stored real-estate market fact JSON", exc);
        }
    }

    private static String joinSummaryParts(String... parts) {
        List<String> selectedParts = new ArrayList<>();
        for (String part : parts) {
            String trimmed = trimToNull(part);
            if (trimmed != null) {
                selectedParts.add(trimmed);
            }
        }
        return String.join(" · ", selectedParts);
    }

    private static String textOrNull(JsonNode node) {
        if (node == null || node.isMissingNode() || node.isNull()) {
            return null;
        }
        String value = node.asText();
        return trimToNull(value);
    }

    private static String formatManwonAsEok(JsonNode manwonNode) {
        if (manwonNode == null || !manwonNode.isNumber()) {
            return "확인 필요";
        }
        double eok = manwonNode.asDouble() / 10000.0;
        return String.format(Locale.KOREA, "%.2f억원", eok);
    }

    private static String formatArea(JsonNode areaNode) {
        if (areaNode == null || !areaNode.isNumber()) {
            return null;
        }
        return String.format(Locale.KOREA, "전용 %.2f㎡", areaNode.asDouble());
    }

    private static String datePart(String label, LocalDate date) {
        return date == null ? null : label + " " + date;
    }

    private static Instant toStartOfDayUtc(LocalDate date) {
        return date == null ? null : date.atStartOfDay().toInstant(ZoneOffset.UTC);
    }

    private static String normalizeLower(String value) {
        return value.trim().toLowerCase(Locale.ROOT);
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

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static Double clampConfidence(Double value) {
        if (value == null) {
            return 0.5;
        }
        return Math.max(0.0, Math.min(1.0, value));
    }
}
