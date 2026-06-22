package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateIndicatorOverviewResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketSummaryItemResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketSummaryResponse;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.Locale;
import java.util.Objects;

@Service
public class RealEstateIndicatorService {

    private final RealEstateMarketFactService marketFactService;

    public RealEstateIndicatorService(RealEstateMarketFactService marketFactService) {
        this.marketFactService = marketFactService;
    }

    @Transactional(readOnly = true)
    public RealEstateIndicatorOverviewResponse overview(String legalDongCode, String period) {
        String normalizedPeriod = normalizePeriod(period);
        RealEstateMarketSummaryResponse summary = marketFactService.summarizeForDashboard(legalDongCode);
        if (summary.items().isEmpty()) {
            return new RealEstateIndicatorOverviewResponse(
                    normalizedPeriod,
                    "empty",
                    null,
                    List.of(),
                    List.of()
            );
        }

        return new RealEstateIndicatorOverviewResponse(
                normalizedPeriod,
                summary.freshness().dataStatus(),
                asOfLabel(summary.freshness().latestAsOf()),
                List.of(priceTransactionGroup(summary)),
                freshnessRows(summary.items())
        );
    }

    private RealEstateIndicatorOverviewResponse.Group priceTransactionGroup(RealEstateMarketSummaryResponse summary) {
        List<RealEstateMarketSummaryItemResponse> items = summary.items();
        boolean stale = items.stream().anyMatch(RealEstateMarketSummaryItemResponse::stale);
        String provider = items.stream()
                .map(RealEstateMarketSummaryItemResponse::provider)
                .filter(Objects::nonNull)
                .findFirst()
                .orElse("unknown");
        String dataStatus = stale ? "stale" : summary.freshness().dataStatus();
        List<String> chips = items.stream()
                .map(item -> "%s %s".formatted(item.label(), item.value()))
                .toList();
        List<RealEstateIndicatorOverviewResponse.Metric> metrics = items.stream()
                .map(item -> new RealEstateIndicatorOverviewResponse.Metric(
                        item.label(),
                        item.value(),
                        "down".equals(item.trend()) ? "down" : "up"
                ))
                .toList();

        return new RealEstateIndicatorOverviewResponse.Group(
                "price-transaction",
                "price & volume",
                "가격 및 거래량",
                "공식 공표 지표로 최신 가격 흐름을 확인합니다",
                changeLabel(items),
                stale ? "down" : "up",
                "한국부동산원과 국토교통부 원천을 provider/asOf 기준으로 구분해 매매, 전세, 거래량 흐름을 우선 표시합니다.",
                chips,
                metrics,
                dataStatus,
                stale,
                provider,
                asOfLabel(summary.freshness().latestAsOf())
        );
    }

    private List<RealEstateIndicatorOverviewResponse.FreshnessRow> freshnessRows(
            List<RealEstateMarketSummaryItemResponse> items
    ) {
        return items.stream()
                .map(RealEstateMarketSummaryItemResponse::provider)
                .filter(Objects::nonNull)
                .distinct()
                .map(provider -> new RealEstateIndicatorOverviewResponse.FreshnessRow(
                        sourceLabel(provider),
                        items.stream().anyMatch(item -> provider.equals(item.provider()) && item.stale())
                                ? "지연 가능"
                                : "공공데이터 반영",
                        usedMetricNames(items, provider)
                ))
                .toList();
    }

    private static String usedMetricNames(List<RealEstateMarketSummaryItemResponse> items, String provider) {
        List<String> labels = items.stream()
                .filter(item -> provider.equals(item.provider()))
                .map(RealEstateMarketSummaryItemResponse::label)
                .distinct()
                .toList();
        if ("molit".equals(provider) && labels.contains("매매 실거래") && labels.contains("전월세 실거래")) {
            return "매매/전월세 실거래";
        }
        return String.join(
                ", ",
                labels
        );
    }

    private static String changeLabel(List<RealEstateMarketSummaryItemResponse> items) {
        return items.stream()
                .map(RealEstateMarketSummaryItemResponse::changePct)
                .filter(Objects::nonNull)
                .findFirst()
                .map(value -> String.format(Locale.KOREA, "%+.2f%%", value))
                .orElse("최신");
    }

    private static String sourceLabel(String provider) {
        return switch (provider) {
            case "molit" -> "국토부 실거래가";
            case "reb" -> "한국부동산원";
            default -> provider;
        };
    }

    private static String asOfLabel(LocalDate asOf) {
        return asOf == null ? null : asOf.toString();
    }

    private static String normalizePeriod(String period) {
        String trimmed = period == null ? "" : period.trim();
        return trimmed.isBlank() ? "month" : trimmed;
    }
}
