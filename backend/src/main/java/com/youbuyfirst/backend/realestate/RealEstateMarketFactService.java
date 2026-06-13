package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketFactRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketFactResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketSummaryFreshnessResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketSummaryItemResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketSummaryResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Objects;

@Service
public class RealEstateMarketFactService {

    private final RealEstateMarketFactRepository repository;
    private final RealEstateRegionRepository regionRepository;
    private final RealEstateTimelineService timelineService;
    private final ObjectMapper objectMapper;

    public RealEstateMarketFactService(
            RealEstateMarketFactRepository repository,
            RealEstateRegionRepository regionRepository,
            RealEstateTimelineService timelineService,
            ObjectMapper objectMapper
    ) {
        this.repository = repository;
        this.regionRepository = regionRepository;
        this.timelineService = timelineService;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public int upsertAll(Collection<RealEstateMarketFactRequest> requests) {
        Instant now = Instant.now();
        int accepted = 0;
        for (RealEstateMarketFactRequest request : requests) {
            String provider = normalizeLower(request.provider());
            String providerDataset = normalizeLower(request.providerDataset());
            String providerObjectId = request.providerObjectId().trim();
            RealEstateMarketFact fact = repository.findByProviderAndProviderDatasetAndProviderObjectId(
                    provider,
                    providerDataset,
                    providerObjectId
            ).orElseGet(() -> new RealEstateMarketFact(provider, providerDataset, providerObjectId));
            String targetType = normalizeLower(request.targetType());
            fact.update(
                    targetType,
                    resolveTargetId(targetType, request.targetId(), request.legalDongCode()),
                    normalizeLower(request.factType()),
                    request.legalDongCode().trim(),
                    request.observedAt(),
                    request.asOf(),
                    request.ingestedAt(),
                    request.sourceUpdatedAt(),
                    writeJson(request.valueJson()),
                    normalizeLower(request.dataStatus()),
                    request.stale(),
                    now
            );
            repository.save(fact);
            timelineService.upsertMarketFactTimeline(fact, now);
            accepted++;
        }
        return accepted;
    }

    @Transactional(readOnly = true)
    public List<RealEstateMarketFactResponse> list(String legalDongCode, String factType, int limit) {
        int boundedLimit = Math.max(1, Math.min(limit, 500));
        return repository.search(
                trimToNull(legalDongCode),
                trimToNull(factType) == null ? null : normalizeLower(factType),
                PageRequest.of(0, boundedLimit)
        ).stream().map(this::toResponse).toList();
    }

    @Transactional(readOnly = true)
    public List<RealEstateMarketFactResponse> listForTarget(String targetId, String factType, int limit) {
        int boundedLimit = Math.max(1, Math.min(limit, 500));
        return repository.searchByTargetId(
                targetId.trim(),
                trimToNull(factType) == null ? null : normalizeLower(factType),
                PageRequest.of(0, boundedLimit)
        ).stream().map(this::toResponse).toList();
    }

    @Transactional(readOnly = true)
    public RealEstateMarketSummaryResponse summarizeForDashboard(String legalDongCode) {
        List<RealEstateMarketFact> facts = repository.search(
                trimToNull(legalDongCode),
                null,
                PageRequest.of(0, 500)
        );
        List<RealEstateMarketSummaryItemResponse> items = new ArrayList<>();
        addLatestSummaryItem(items, facts, "apt_trade");
        addLatestSummaryItem(items, facts, "apt_rent");
        return new RealEstateMarketSummaryResponse(items, buildFreshness(items, facts));
    }

    private RealEstateMarketFactResponse toResponse(RealEstateMarketFact fact) {
        return new RealEstateMarketFactResponse(
                fact.getTargetType(),
                fact.getTargetId(),
                fact.getFactType(),
                fact.getProvider(),
                fact.getProviderDataset(),
                fact.getProviderObjectId(),
                fact.getLegalDongCode(),
                fact.getObservedAt(),
                fact.getAsOf(),
                fact.getIngestedAt(),
                fact.getSourceUpdatedAt(),
                readJson(fact.getValueJson()),
                fact.getDataStatus(),
                fact.isStale()
        );
    }

    private JsonNode readJson(String value) {
        try {
            return objectMapper.readTree(value);
        } catch (JsonProcessingException exc) {
            throw new IllegalStateException("invalid stored real-estate market fact JSON", exc);
        }
    }

    private String writeJson(JsonNode value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException exc) {
            throw new IllegalArgumentException("invalid real-estate market fact JSON", exc);
        }
    }

    private void addLatestSummaryItem(
            List<RealEstateMarketSummaryItemResponse> items,
            List<RealEstateMarketFact> facts,
            String factType
    ) {
        facts.stream()
                .filter(fact -> factType.equals(fact.getFactType()))
                .findFirst()
                .map(this::toSummaryItem)
                .ifPresent(items::add);
    }

    private RealEstateMarketSummaryItemResponse toSummaryItem(RealEstateMarketFact fact) {
        return new RealEstateMarketSummaryItemResponse(
                summaryLabel(fact.getFactType()),
                summaryValue(fact),
                null,
                updatedLabel(fact),
                trend(fact),
                fact.getDataStatus(),
                fact.isStale(),
                fact.getProvider(),
                fact.getFactType(),
                fact.getLegalDongCode()
        );
    }

    private RealEstateMarketSummaryFreshnessResponse buildFreshness(
            List<RealEstateMarketSummaryItemResponse> items,
            List<RealEstateMarketFact> facts
    ) {
        List<RealEstateMarketFact> selectedFacts = facts.stream()
                .filter(fact -> items.stream().anyMatch(item -> item.factType().equals(fact.getFactType())))
                .filter(fact -> items.stream().anyMatch(item -> item.provider().equals(fact.getProvider())))
                .toList();
        if (items.isEmpty()) {
            return new RealEstateMarketSummaryFreshnessResponse(1, 0, null, "empty");
        }
        int staleCount = (int) items.stream().filter(RealEstateMarketSummaryItemResponse::stale).count();
        int sourceCount = (int) items.stream()
                .map(RealEstateMarketSummaryItemResponse::provider)
                .filter(Objects::nonNull)
                .distinct()
                .count();
        LocalDate latestAsOf = selectedFacts.stream()
                .map(RealEstateMarketFact::getAsOf)
                .filter(Objects::nonNull)
                .max(LocalDate::compareTo)
                .orElse(null);
        String dataStatus = staleCount > 0
                ? "stale"
                : items.stream().allMatch(item -> "ok".equals(item.dataStatus())) ? "ok" : "partial";
        return new RealEstateMarketSummaryFreshnessResponse(staleCount, sourceCount, latestAsOf, dataStatus);
    }

    private String summaryLabel(String factType) {
        return switch (factType) {
            case "apt_trade" -> "매매 실거래";
            case "apt_rent" -> "전월세 실거래";
            default -> "시장 데이터";
        };
    }

    private String summaryValue(RealEstateMarketFact fact) {
        JsonNode valueJson = readJson(fact.getValueJson());
        return switch (fact.getFactType()) {
            case "apt_trade" -> formatManwonAsEok(valueJson.path("dealAmountManwon"));
            case "apt_rent" -> "보증금 %s / 월세 %s만원".formatted(
                    formatManwonAsEok(firstNode(valueJson, "depositAmountManwon", "depositManwon")),
                    firstNode(valueJson, "monthlyRentAmountManwon", "monthlyRentManwon").asText("확인 필요")
            );
            default -> "확인 필요";
        };
    }

    private String updatedLabel(RealEstateMarketFact fact) {
        return "%s · 계약 %s · 기준 %s".formatted(
                providerLabel(fact.getProvider()),
                fact.getObservedAt(),
                fact.getAsOf()
        );
    }

    private String trend(RealEstateMarketFact fact) {
        if (fact.isStale() || !"ok".equals(fact.getDataStatus())) {
            return "down";
        }
        return "up";
    }

    private String providerLabel(String provider) {
        return switch (provider) {
            case "molit" -> "국토교통부";
            case "reb" -> "한국부동산원";
            default -> provider;
        };
    }

    private String formatManwonAsEok(JsonNode manwonNode) {
        if (!manwonNode.isNumber()) {
            return "확인 필요";
        }
        double eok = manwonNode.asDouble() / 10000.0;
        return String.format(Locale.KOREA, "%.2f억원", eok);
    }

    private JsonNode firstNode(JsonNode valueJson, String firstFieldName, String fallbackFieldName) {
        JsonNode firstNode = valueJson.path(firstFieldName);
        if (!firstNode.isMissingNode() && !firstNode.isNull()) {
            return firstNode;
        }
        return valueJson.path(fallbackFieldName);
    }

    private static String normalizeLower(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
    }

    private String resolveTargetId(String targetType, String requestedTargetId, String legalDongCode) {
        String explicitTargetId = trimToNull(requestedTargetId);
        if (explicitTargetId != null || !"region".equals(targetType)) {
            return explicitTargetId;
        }
        String normalizedLegalDongCode = trimToNull(legalDongCode);
        if (normalizedLegalDongCode == null) {
            return null;
        }
        return regionRepository.findFirstByLegalDongCode(normalizedLegalDongCode)
                .map(RealEstateRegion::getTargetId)
                .orElse(null);
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }
}
