package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.ChartCandleBarRequest;
import com.youbuyfirst.backend.market.dto.ChartCandleBarResponse;
import com.youbuyfirst.backend.market.dto.ChartCandleDisplayPolicyResponse;
import com.youbuyfirst.backend.market.dto.ChartCandleResponse;
import com.youbuyfirst.backend.market.dto.ChartCandleSetRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Duration;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

@Service
public class ChartCandleService {

    private static final Set<String> ALLOWED_RANGES = Set.of("1M", "3M", "6M", "1Y", "3Y", "5Y");
    private static final Set<String> ALLOWED_INTERVALS = Set.of("1d", "1wk", "1mo");
    private static final Map<String, Integer> MAX_BARS_BY_RANGE = Map.of(
            "1M", 22,
            "3M", 66,
            "6M", 132,
            "1Y", 252,
            "3Y", 756,
            "5Y", 1260
    );

    private final ChartCandleSetRepository repository;
    private final ChartCandleRefreshRequestService refreshRequestService;
    private final MarketSymbolResolver symbolResolver;
    private final Duration staleAfter;

    public ChartCandleService(
            ChartCandleSetRepository repository,
            ChartCandleRefreshRequestService refreshRequestService,
            MarketSymbolResolver symbolResolver,
            @Value("${app.market.chart-candle-stale-minutes:2160}") long chartCandleStaleMinutes
    ) {
        this.repository = repository;
        this.refreshRequestService = refreshRequestService;
        this.symbolResolver = symbolResolver;
        this.staleAfter = Duration.ofMinutes(chartCandleStaleMinutes);
    }

    @Transactional
    public void upsertAll(List<ChartCandleSetRequest> requests) {
        Instant collectedAt = Instant.now();
        for (ChartCandleSetRequest request : requests) {
            String symbol = normalizeUpper(request.symbol());
            String range = normalizeRange(request.range());
            String interval = normalizeInterval(request.interval());
            validateRangeAndInterval(range, interval);
            List<ChartCandleBarRequest> bars = boundedBars(request.bars(), range);
            String dataStatus = bars.isEmpty() ? "INSUFFICIENT" : normalizeUpper(request.dataStatus());

            Optional<ChartCandleSet> existingCandleSet = repository.findBySymbolIgnoreCaseAndRangeLabelAndCandleInterval(
                    symbol,
                    range,
                    interval
            );
            ChartCandleSet candleSet = existingCandleSet.orElseGet(() -> new ChartCandleSet(symbol, range, interval));
            if (existingCandleSet.isPresent()) {
                candleSet.clearBars();
                repository.saveAndFlush(candleSet);
            }
            candleSet.update(
                    request.name().trim(),
                    normalizeUpper(request.market()),
                    normalizeUpper(request.currency()),
                    request.provider().trim(),
                    request.delayLabel().trim(),
                    request.asOf(),
                    dataStatus,
                    collectedAt,
                    bars
            );
            repository.save(candleSet);
            refreshRequestService.markCompleted(symbol, range, interval);
        }
    }

    @Transactional
    public ChartCandleResponse get(String symbol, String range, String interval) {
        String normalizedSymbol = symbolResolver.normalizeProviderSymbol(normalizeRequiredSymbol(symbol));
        String normalizedRange = normalizeRange(range == null || range.isBlank() ? "3M" : range);
        String normalizedInterval = normalizeInterval(interval == null || interval.isBlank() ? "1d" : interval);
        validateRangeAndInterval(normalizedRange, normalizedInterval);

        Optional<ChartCandleSet> existing = repository.findBySymbolIgnoreCaseAndRangeLabelAndCandleInterval(
                normalizedSymbol,
                normalizedRange,
                normalizedInterval
        );
        if (existing.isPresent()) {
            if (isStale(existing.get())) {
                refreshRequestService.request(normalizedSymbol, normalizedRange, normalizedInterval);
            }
            return toResponse(existing.get());
        }

        refreshRequestService.request(normalizedSymbol, normalizedRange, normalizedInterval);
        return insufficientResponse(normalizedSymbol, normalizedRange, normalizedInterval);
    }

    private ChartCandleResponse toResponse(ChartCandleSet candleSet) {
        boolean stale = isStale(candleSet);
        List<ChartCandleBarResponse> bars = candleSet.getBars().stream()
                .sorted(Comparator.comparing(ChartCandle::getTradeDate))
                .map(bar -> new ChartCandleBarResponse(
                        bar.getTradeDate(),
                        bar.getOpen(),
                        bar.getHigh(),
                        bar.getLow(),
                        bar.getClose(),
                        bar.getVolume()
                ))
                .toList();
        String dataStatus = bars.isEmpty() ? "INSUFFICIENT" : (stale ? "STALE" : candleSet.getDataStatus());
        return new ChartCandleResponse(
                candleSet.getSymbol(),
                candleSet.getName(),
                candleSet.getMarket(),
                candleSet.getCurrency(),
                candleSet.getRangeLabel(),
                candleSet.getCandleInterval(),
                candleSet.getProvider(),
                candleSet.getDelayLabel(),
                candleSet.getAsOf(),
                stale,
                dataStatus,
                bars,
                displayPolicy(candleSet.getRangeLabel())
        );
    }

    private ChartCandleResponse insufficientResponse(String symbol, String range, String interval) {
        MarketInstrument instrument = symbolResolver.resolve(symbol);
        return new ChartCandleResponse(
                instrument.symbol(),
                instrument.name(),
                instrument.market(),
                instrument.currency(),
                range,
                interval,
                symbolResolver.providerName(instrument.market()),
                symbolResolver.delayLabel(instrument),
                Instant.EPOCH,
                true,
                "INSUFFICIENT",
                List.of(),
                displayPolicy(range)
        );
    }

    private boolean isStale(ChartCandleSet candleSet) {
        if ("STALE".equalsIgnoreCase(candleSet.getDataStatus())) {
            return true;
        }
        return candleSet.getAsOf().plus(staleAfter).isBefore(Instant.now());
    }

    private static List<ChartCandleBarRequest> boundedBars(List<ChartCandleBarRequest> bars, String range) {
        List<ChartCandleBarRequest> sorted = bars.stream()
                .sorted(Comparator.comparing(ChartCandleBarRequest::date))
                .toList();
        int from = Math.max(0, sorted.size() - maxBarsForRange(range));
        return sorted.subList(from, sorted.size());
    }

    private static ChartCandleDisplayPolicyResponse displayPolicy(String range) {
        return new ChartCandleDisplayPolicyResponse(true, false, false, maxBarsForRange(range));
    }

    private static int maxBarsForRange(String range) {
        return MAX_BARS_BY_RANGE.getOrDefault(range, MAX_BARS_BY_RANGE.get("5Y"));
    }

    private static void validateRangeAndInterval(String range, String interval) {
        if (!ALLOWED_RANGES.contains(range)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "unsupported chart range: " + range);
        }
        if (!ALLOWED_INTERVALS.contains(interval)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "unsupported chart interval: " + interval);
        }
    }

    private static String normalizeRequiredSymbol(String value) {
        String normalized = normalizeUpper(value);
        if (normalized.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "symbol is required");
        }
        return normalized;
    }

    private static String normalizeRange(String value) {
        return normalizeUpper(value);
    }

    private static String normalizeInterval(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
    }

    private static String normalizeUpper(String value) {
        return value == null ? "" : value.trim().toUpperCase(Locale.ROOT);
    }

}
