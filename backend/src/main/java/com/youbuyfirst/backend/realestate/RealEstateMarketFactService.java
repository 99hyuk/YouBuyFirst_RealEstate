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

import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;

@Service
public class RealEstateMarketFactService {

    private static final List<String> DASHBOARD_SUMMARY_FACT_TYPES = List.of(
            "sale_price_index_change_pct",
            "jeonse_price_index_change_pct",
            "apartment_trade_volume",
            "apt_trade",
            "apt_rent"
    );
    private static final Map<String, List<String>> OFFICIAL_PROVIDER_DATASETS_BY_FACT_TYPE = Map.of(
            "apt_trade", List.of("molit_apt_trade"),
            "apt_rent", List.of("molit_apt_rent"),
            "official_apartment_price", List.of("molit_official_apartment_price_csv")
    );

    private final RealEstateMarketFactRepository repository;
    private final RealEstateRegionRepository regionRepository;
    private final RealEstateComplexRepository complexRepository;
    private final RealEstateTimelineService timelineService;
    private final ObjectMapper objectMapper;

    public RealEstateMarketFactService(
            RealEstateMarketFactRepository repository,
            RealEstateRegionRepository regionRepository,
            RealEstateComplexRepository complexRepository,
            RealEstateTimelineService timelineService,
            ObjectMapper objectMapper
    ) {
        this.repository = repository;
        this.regionRepository = regionRepository;
        this.complexRepository = complexRepository;
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
    public List<RealEstateMarketFactResponse> list(String targetId, String legalDongCode, String factType, String dealYm, int limit, int page) {
        int boundedLimit = Math.max(1, Math.min(limit, 500));
        int boundedPage = Math.max(0, page);
        String normalizedTargetId = trimToNull(targetId);
        String normalizedLegalDongCode = trimToNull(legalDongCode);
        String normalizedFactType = trimToNull(factType) == null ? null : normalizeLower(factType);
        LocalDate dealMonth = parseDealMonth(dealYm);
        PageRequest pageRequest = PageRequest.of(boundedPage, boundedLimit);
        List<RealEstateMarketFact> facts;
        if (dealMonth != null) {
            // 거래월(YYYYMM) 필터가 있으면 단일 쿼리로 처리(기간 비교용 월별 조회).
            facts = repository.search(normalizedTargetId, normalizedLegalDongCode, normalizedFactType, dealMonth, pageRequest);
        } else {
            facts = findListFacts(normalizedTargetId, normalizedLegalDongCode, normalizedFactType, pageRequest);
        }
        return facts.stream().map(this::toResponse).toList();
    }

    private static LocalDate parseDealMonth(String dealYm) {
        String normalized = trimToNull(dealYm);
        if (normalized == null || !normalized.matches("\\d{6}")) {
            return null;
        }
        int year = Integer.parseInt(normalized.substring(0, 4));
        int month = Integer.parseInt(normalized.substring(4, 6));
        if (month < 1 || month > 12) {
            return null;
        }
        return LocalDate.of(year, month, 1);
    }

    @Transactional(readOnly = true)
    public List<RealEstateMarketFactResponse> listForTarget(String targetId, String factType, int limit, boolean officialOnly) {
        int boundedLimit = Math.max(1, Math.min(limit, 500));
        String normalizedTargetId = targetId.trim();
        String normalizedFactType = trimToNull(factType) == null ? null : normalizeLower(factType);
        List<RealEstateMarketFact> facts = officialOnly
                ? findOfficialFactsForTarget(normalizedTargetId, normalizedFactType, boundedLimit)
                : repository.searchByTargetId(
                        normalizedTargetId,
                        normalizedFactType,
                        PageRequest.of(0, boundedLimit)
                );
        return facts.stream().map(this::toResponse).toList();
    }

    @Transactional(readOnly = true)
    public RealEstateMarketSummaryResponse summarizeForDashboard(String legalDongCode) {
        String normalizedLegalDongCode = trimToNull(legalDongCode);
        List<RealEstateMarketFact> facts = DASHBOARD_SUMMARY_FACT_TYPES.stream()
                .map(factType -> findLatestSummaryFact(normalizedLegalDongCode, factType))
                .flatMap(List::stream)
                .toList();
        List<RealEstateMarketSummaryItemResponse> items = new ArrayList<>();
        addLatestSummaryItem(items, facts, "sale_price_index_change_pct");
        addLatestSummaryItem(items, facts, "jeonse_price_index_change_pct");
        addLatestSummaryItem(items, facts, "apartment_trade_volume");
        addLatestSummaryItem(items, facts, "apt_trade");
        addLatestSummaryItem(items, facts, "apt_rent");
        return new RealEstateMarketSummaryResponse(items, buildFreshness(items, facts));
    }

    private List<RealEstateMarketFact> findListFacts(
            String targetId,
            String legalDongCode,
            String factType,
            PageRequest pageRequest
    ) {
        if (targetId == null && legalDongCode == null && factType == null) {
            return repository.findLatest(pageRequest);
        }
        if (targetId == null && legalDongCode != null && factType == null) {
            return repository.findLatestByLegalDongCode(legalDongCode, pageRequest);
        }
        if (targetId == null && legalDongCode == null) {
            return repository.findLatestByFactType(factType, pageRequest);
        }
        if (targetId == null) {
            return repository.findLatestByLegalDongCodeAndFactType(legalDongCode, factType, pageRequest);
        }
        return repository.search(targetId, legalDongCode, factType, null, pageRequest);
    }

    private List<RealEstateMarketFact> findLatestSummaryFact(String legalDongCode, String factType) {
        PageRequest pageRequest = PageRequest.of(0, 1);
        if (legalDongCode == null) {
            return repository.findLatestByFactType(factType, pageRequest);
        }
        return repository.findLatestByLegalDongCodeAndFactType(legalDongCode, factType, pageRequest);
    }

    private List<RealEstateMarketFact> findOfficialFactsForTarget(String targetId, String factType, int limit) {
        List<String> providerDatasets = officialProviderDatasets(factType);
        if (providerDatasets.isEmpty()) {
            return List.of();
        }

        LinkedHashMap<String, RealEstateMarketFact> merged = new LinkedHashMap<>();
        repository.searchByTargetIdAndProviderDatasetIn(
                        targetId,
                        factType,
                        providerDatasets,
                        PageRequest.of(0, limit)
                )
                .forEach(fact -> merged.put(marketFactKey(fact), fact));
        if (merged.size() >= limit) {
            return merged.values().stream().limit(limit).toList();
        }

        complexRepository.findById(targetId)
                .ifPresent(complex -> findOfficialFactsForComplex(complex, factType, providerDatasets, limit)
                        .forEach(fact -> merged.putIfAbsent(marketFactKey(fact), fact)));
        return merged.values().stream()
                .sorted((left, right) -> {
                    int observedCompare = right.getObservedAt().compareTo(left.getObservedAt());
                    if (observedCompare != 0) {
                        return observedCompare;
                    }
                    return left.getProviderObjectId().compareTo(right.getProviderObjectId());
                })
                .limit(limit)
                .toList();
    }

    private List<RealEstateMarketFact> findOfficialFactsForComplex(
            RealEstateComplex complex,
            String factType,
            List<String> providerDatasets,
            int limit
    ) {
        if (factType == null || !List.of("apt_trade", "apt_rent", "official_apartment_price").contains(factType)) {
            return List.of();
        }
        RealEstateTarget target = complex.getTarget();
        String displayName = target == null ? null : target.getDisplayName();
        if (trimToNull(displayName) == null) {
            return List.of();
        }

        LinkedHashMap<String, RealEstateMarketFact> matched = new LinkedHashMap<>();
        int candidateLimit = Math.max(1000, Math.min(5000, limit * 1000));
        for (String legalDongCode : officialLookupLegalDongCodes(complex.getLegalDongCode())) {
            repository.findLatestByLegalDongCodeAndFactTypeAndProviderDatasetIn(
                            legalDongCode,
                            factType,
                            providerDatasets,
                            PageRequest.of(0, candidateLimit)
                    )
                    .stream()
                    .filter(fact -> matchesComplexOfficialFact(complex, displayName, fact))
                    .forEach(fact -> matched.putIfAbsent(marketFactKey(fact), fact));
            if (matched.size() >= limit) {
                break;
            }
        }
        return matched.values().stream().limit(limit).toList();
    }

    private List<String> officialProviderDatasets(String factType) {
        if (factType == null) {
            return OFFICIAL_PROVIDER_DATASETS_BY_FACT_TYPE.values().stream()
                    .flatMap(Collection::stream)
                    .toList();
        }
        return OFFICIAL_PROVIDER_DATASETS_BY_FACT_TYPE.getOrDefault(factType, List.of());
    }

    private List<String> officialLookupLegalDongCodes(String legalDongCode) {
        String normalized = trimToNull(legalDongCode);
        if (normalized == null) {
            return List.of();
        }
        List<String> values = new ArrayList<>();
        values.add(normalized);
        if (normalized.length() >= 5) {
            String sigunguCode = normalized.substring(0, 5);
            if (!values.contains(sigunguCode)) {
                values.add(sigunguCode);
            }
        }
        return values;
    }

    private boolean matchesComplexOfficialFact(
            RealEstateComplex complex,
            String displayName,
            RealEstateMarketFact fact
    ) {
        JsonNode valueJson = readJson(fact.getValueJson());
        String apartmentName = valueJson.path("apartmentName").asText(null);
        if (!matchesNormalizedName(displayName, apartmentName)) {
            return false;
        }

        String addressKey = normalizeComparableText("%s %s %s".formatted(
                defaultString(complex.getJibunAddress()),
                defaultString(complex.getRoadAddress()),
                defaultString(complex.getNormalizedAddress())
        ));
        if (addressKey.isBlank()) {
            return true;
        }

        String legalDongNameKey = normalizeComparableText(valueJson.path("legalDongName").asText(""));
        if (!legalDongNameKey.isBlank() && !addressKey.contains(legalDongNameKey)) {
            return false;
        }

        String jibunKey = normalizeComparableText(valueJson.path("jibun").asText(""));
        return jibunKey.isBlank() || addressKey.contains(jibunKey);
    }

    private static boolean matchesNormalizedName(String left, String right) {
        String leftKey = normalizeComparableText(left);
        String rightKey = normalizeComparableText(right);
        if (leftKey.isBlank() || rightKey.isBlank()) {
            return false;
        }
        return leftKey.equals(rightKey) || leftKey.endsWith(rightKey) || rightKey.endsWith(leftKey);
    }

    private static String normalizeComparableText(String value) {
        if (value == null) {
            return "";
        }
        StringBuilder normalized = new StringBuilder();
        value.toLowerCase(Locale.ROOT).codePoints()
                .filter(Character::isLetterOrDigit)
                .forEach(normalized::appendCodePoint);
        return normalized.toString();
    }

    private static String defaultString(String value) {
        return value == null ? "" : value;
    }

    private static String marketFactKey(RealEstateMarketFact fact) {
        return "%s:%s:%s".formatted(
                fact.getProvider(),
                fact.getProviderDataset(),
                fact.getProviderObjectId()
        );
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
                summaryChangePct(fact),
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
            case "sale_price_index_change_pct" -> "매매가격지수";
            case "jeonse_price_index_change_pct" -> "전세가격지수";
            case "apartment_trade_volume" -> "아파트 매매거래";
            case "apt_trade" -> "매매 실거래";
            case "apt_rent" -> "전월세 실거래";
            default -> "시장 데이터";
        };
    }

    private String summaryValue(RealEstateMarketFact fact) {
        JsonNode valueJson = readJson(fact.getValueJson());
        return switch (fact.getFactType()) {
            case "sale_price_index_change_pct", "jeonse_price_index_change_pct" -> formatValueWithUnit(valueJson);
            case "apartment_trade_volume" -> formatCount(valueJson.path("value"), valueJson.path("unit").asText("건"));
            case "apt_trade" -> formatManwonAsEok(valueJson.path("dealAmountManwon"));
            case "apt_rent" -> "보증금 %s / 월세 %s만원".formatted(
                    formatManwonAsEok(firstNode(valueJson, "depositAmountManwon", "depositManwon")),
                    firstNode(valueJson, "monthlyRentAmountManwon", "monthlyRentManwon").asText("확인 필요")
            );
            default -> "확인 필요";
        };
    }

    private Double summaryChangePct(RealEstateMarketFact fact) {
        if (!List.of("sale_price_index_change_pct", "jeonse_price_index_change_pct").contains(fact.getFactType())) {
            return null;
        }
        JsonNode valueNode = readJson(fact.getValueJson()).path("value");
        return valueNode.isNumber() ? valueNode.asDouble() : null;
    }

    private String updatedLabel(RealEstateMarketFact fact) {
        return "%s · %s %s · 기준 %s".formatted(
                providerLabel(fact.getProvider()),
                observedLabel(fact.getFactType()),
                fact.getObservedAt(),
                fact.getAsOf()
        );
    }

    private String observedLabel(String factType) {
        return switch (factType) {
            case "apt_trade", "apt_rent" -> "계약";
            default -> "관측";
        };
    }

    private String trend(RealEstateMarketFact fact) {
        if (fact.isStale() || !"ok".equals(fact.getDataStatus())) {
            return "down";
        }
        return switch (fact.getFactType()) {
            case "sale_price_index_change_pct", "jeonse_price_index_change_pct" -> {
                JsonNode valueNode = readJson(fact.getValueJson()).path("value");
                yield valueNode.isNumber() && valueNode.asDouble() < 0 ? "down" : "up";
            }
            default -> "up";
        };
    }

    private String providerLabel(String provider) {
        return switch (provider) {
            case "molit" -> "국토교통부";
            case "reb" -> "한국부동산원";
            default -> provider;
        };
    }

    private String formatValueWithUnit(JsonNode valueJson) {
        JsonNode valueNode = valueJson.path("value");
        if (!valueNode.isNumber()) {
            return "확인 필요";
        }
        String unit = valueJson.path("unit").asText("");
        if ("%".equals(unit)) {
            return String.format(Locale.KOREA, "%+.2f%%", valueNode.asDouble());
        }
        return String.format(Locale.KOREA, "%,.2f%s", valueNode.asDouble(), unit);
    }

    private String formatCount(JsonNode valueNode, String unit) {
        if (!valueNode.isNumber()) {
            return "확인 필요";
        }
        return String.format(Locale.KOREA, "%,d%s", valueNode.asLong(), unit);
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
