package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.BollingerBandsResponse;
import com.youbuyfirst.backend.market.dto.BollingerBandPointResponse;
import com.youbuyfirst.backend.market.dto.RsiPointResponse;
import com.youbuyfirst.backend.market.dto.RsiResponse;
import com.youbuyfirst.backend.market.dto.TechnicalIndicatorResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;

@Service
public class TechnicalIndicatorService {

    private static final Set<String> ALLOWED_RANGES = Set.of("1M", "3M", "6M", "1Y", "3Y", "5Y");
    private static final Set<String> ALLOWED_INTERVALS = Set.of("1d", "1wk", "1mo");

    private final ChartCandleSetRepository chartCandleSetRepository;
    private final MarketSymbolResolver symbolResolver;
    private final Duration staleAfter;

    public TechnicalIndicatorService(
            ChartCandleSetRepository chartCandleSetRepository,
            MarketSymbolResolver symbolResolver,
            @Value("${app.market.chart-candle-stale-minutes:30}") long chartCandleStaleMinutes
    ) {
        this.chartCandleSetRepository = chartCandleSetRepository;
        this.symbolResolver = symbolResolver;
        this.staleAfter = Duration.ofMinutes(chartCandleStaleMinutes);
    }

    @Transactional(readOnly = true)
    public TechnicalIndicatorResponse get(
            String symbol,
            String range,
            String interval,
            Integer rsiPeriod,
            Integer bollingerPeriod,
            BigDecimal bollingerMultiplier
    ) {
        MarketInstrument instrument = symbolResolver.resolve(normalizeRequiredSymbol(symbol));
        String normalizedRange = normalizeRange(range == null || range.isBlank() ? "3M" : range);
        String normalizedInterval = normalizeInterval(interval == null || interval.isBlank() ? "1d" : interval);
        validateRangeAndInterval(normalizedRange, normalizedInterval);
        int boundedRsiPeriod = boundedPeriod(rsiPeriod == null ? 14 : rsiPeriod);
        int boundedBollingerPeriod = boundedPeriod(bollingerPeriod == null ? 20 : bollingerPeriod);
        BigDecimal multiplier = (bollingerMultiplier == null ? new BigDecimal("2.00") : bollingerMultiplier)
                .setScale(2, RoundingMode.HALF_UP);

        return findCandleSet(instrument, normalizedRange, normalizedInterval)
                .map(candleSet -> responseFrom(candleSet, boundedRsiPeriod, boundedBollingerPeriod, multiplier))
                .orElseGet(() -> insufficientResponse(
                        instrument,
                        normalizedRange,
                        normalizedInterval,
                        boundedRsiPeriod,
                        boundedBollingerPeriod,
                        multiplier
                ));
    }

    private TechnicalIndicatorResponse responseFrom(
            ChartCandleSet candleSet,
            int rsiPeriod,
            int bollingerPeriod,
            BigDecimal multiplier
    ) {
        boolean stale = isStale(candleSet);
        String dataStatus = candleSet.getBars().isEmpty() ? "INSUFFICIENT" : (stale ? "STALE" : candleSet.getDataStatus());
        List<ChartCandle> bars = candleSet.getBars().stream()
                .sorted(Comparator.comparing(ChartCandle::getTradeDate))
                .toList();
        return new TechnicalIndicatorResponse(
                candleSet.getSymbol(),
                candleSet.getName(),
                candleSet.getMarket(),
                candleSet.getCurrency(),
                candleSet.getRangeLabel(),
                candleSet.getCandleInterval(),
                "backend-derived",
                candleSet.getProvider(),
                candleSet.getDelayLabel(),
                candleSet.getAsOf(),
                stale,
                dataStatus,
                new RsiResponse(rsiPeriod, rsiPoints(bars, rsiPeriod)),
                new BollingerBandsResponse(bollingerPeriod, multiplier, bollingerPoints(bars, bollingerPeriod, multiplier))
        );
    }

    private TechnicalIndicatorResponse insufficientResponse(
            MarketInstrument instrument,
            String range,
            String interval,
            int rsiPeriod,
            int bollingerPeriod,
            BigDecimal multiplier
    ) {
        return new TechnicalIndicatorResponse(
                instrument.symbol(),
                instrument.name(),
                instrument.market(),
                instrument.currency(),
                range,
                interval,
                "backend-derived",
                symbolResolver.providerName(instrument.market()),
                symbolResolver.delayLabel(instrument),
                Instant.EPOCH,
                true,
                "INSUFFICIENT",
                new RsiResponse(rsiPeriod, List.of()),
                new BollingerBandsResponse(bollingerPeriod, multiplier, List.of())
        );
    }

    private Optional<ChartCandleSet> findCandleSet(MarketInstrument instrument, String range, String interval) {
        if (instrument.instrumentId() != null) {
            Optional<ChartCandleSet> byInstrument = chartCandleSetRepository.findFirstByInstrumentIdAndRangeLabelAndCandleInterval(
                    instrument.instrumentId(),
                    range,
                    interval
            );
            if (byInstrument.isPresent()) {
                return byInstrument;
            }
        }
        return chartCandleSetRepository.findBySymbolIgnoreCaseAndRangeLabelAndCandleInterval(
                instrument.symbol(),
                range,
                interval
        );
    }

    private List<RsiPointResponse> rsiPoints(List<ChartCandle> bars, int period) {
        return java.util.stream.IntStream.range(0, bars.size())
                .mapToObj(index -> {
                    ChartCandle bar = bars.get(index);
                    if (index < period) {
                        return new RsiPointResponse(bar.getTradeDate(), null);
                    }

                    BigDecimal gains = BigDecimal.ZERO;
                    BigDecimal losses = BigDecimal.ZERO;
                    for (int cursor = index - period + 1; cursor <= index; cursor += 1) {
                        BigDecimal delta = bars.get(cursor).getClose().subtract(bars.get(cursor - 1).getClose());
                        if (delta.signum() >= 0) {
                            gains = gains.add(delta);
                        } else {
                            losses = losses.add(delta.abs());
                        }
                    }

                    if (losses.signum() == 0) {
                        BigDecimal value = gains.signum() == 0 ? new BigDecimal("50.00") : new BigDecimal("100.00");
                        return new RsiPointResponse(bar.getTradeDate(), value);
                    }

                    BigDecimal averageGain = gains.divide(BigDecimal.valueOf(period), 10, RoundingMode.HALF_UP);
                    BigDecimal averageLoss = losses.divide(BigDecimal.valueOf(period), 10, RoundingMode.HALF_UP);
                    BigDecimal relativeStrength = averageGain.divide(averageLoss, 10, RoundingMode.HALF_UP);
                    BigDecimal value = BigDecimal.valueOf(100)
                            .subtract(BigDecimal.valueOf(100).divide(BigDecimal.ONE.add(relativeStrength), 10, RoundingMode.HALF_UP));
                    return new RsiPointResponse(bar.getTradeDate(), rounded(value));
                })
                .toList();
    }

    private List<BollingerBandPointResponse> bollingerPoints(List<ChartCandle> bars, int period, BigDecimal multiplier) {
        double multiplierValue = multiplier.doubleValue();
        return java.util.stream.IntStream.range(0, bars.size())
                .mapToObj(index -> {
                    ChartCandle bar = bars.get(index);
                    if (index < period - 1) {
                        return new BollingerBandPointResponse(bar.getTradeDate(), null, null, null);
                    }

                    List<ChartCandle> window = bars.subList(index - period + 1, index + 1);
                    double middle = window.stream()
                            .mapToDouble(item -> item.getClose().doubleValue())
                            .average()
                            .orElse(0);
                    double variance = window.stream()
                            .mapToDouble(item -> Math.pow(item.getClose().doubleValue() - middle, 2))
                            .average()
                            .orElse(0);
                    double bandWidth = Math.sqrt(variance) * multiplierValue;
                    return new BollingerBandPointResponse(
                            bar.getTradeDate(),
                            rounded(middle + bandWidth),
                            rounded(middle),
                            rounded(middle - bandWidth)
                    );
                })
                .toList();
    }

    private boolean isStale(ChartCandleSet candleSet) {
        if ("STALE".equalsIgnoreCase(candleSet.getDataStatus())) {
            return true;
        }
        return candleSet.getAsOf().plus(staleAfter).isBefore(Instant.now());
    }

    private static int boundedPeriod(int value) {
        if (value < 2 || value > 200) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "indicator period must be between 2 and 200");
        }
        return value;
    }

    private static void validateRangeAndInterval(String range, String interval) {
        if (!ALLOWED_RANGES.contains(range)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "unsupported chart range: " + range);
        }
        if (!ALLOWED_INTERVALS.contains(interval)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "unsupported chart interval: " + interval);
        }
    }

    private static BigDecimal rounded(double value) {
        return BigDecimal.valueOf(value).setScale(2, RoundingMode.HALF_UP);
    }

    private static BigDecimal rounded(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
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
