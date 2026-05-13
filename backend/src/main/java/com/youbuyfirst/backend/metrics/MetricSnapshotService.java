package com.youbuyfirst.backend.metrics;

import com.youbuyfirst.backend.instrument.Instrument;
import com.youbuyfirst.backend.sentiment.SentimentAnalysis;
import com.youbuyfirst.backend.sentiment.SentimentAnalysisRepository;
import com.youbuyfirst.backend.sentiment.SentimentLabel;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class MetricSnapshotService {

    private static final Duration WINDOW = Duration.ofMinutes(30);

    private final SentimentAnalysisRepository sentimentAnalysisRepository;
    private final MetricSnapshotRepository metricSnapshotRepository;

    public MetricSnapshotService(SentimentAnalysisRepository sentimentAnalysisRepository, MetricSnapshotRepository metricSnapshotRepository) {
        this.sentimentAnalysisRepository = sentimentAnalysisRepository;
        this.metricSnapshotRepository = metricSnapshotRepository;
    }

    public void rebuildWindowsTouchedBy(List<Instant> publishedTimes) {
        publishedTimes.stream()
                .map(MetricSnapshotService::floorToWindow)
                .distinct()
                .forEach(this::rebuildWindow);
    }

    private void rebuildWindow(Instant windowStart) {
        Instant windowEnd = windowStart.plus(WINDOW);
        metricSnapshotRepository.deleteByWindowStart(windowStart);
        List<SentimentAnalysis> analyses = sentimentAnalysisRepository.findAnalysesInWindow(windowStart, windowEnd);

        Map<Instrument, Counter> counters = new HashMap<>();
        for (SentimentAnalysis analysis : analyses) {
            counters.computeIfAbsent(analysis.getInstrument(), ignored -> new Counter())
                    .add(analysis.getSentiment());
        }

        List<MetricSnapshot> snapshots = counters.entrySet().stream()
                .map(entry -> toSnapshot(entry.getKey(), entry.getValue(), windowStart, windowEnd))
                .toList();
        metricSnapshotRepository.saveAll(snapshots);
    }

    private MetricSnapshot toSnapshot(Instrument instrument, Counter counter, Instant windowStart, Instant windowEnd) {
        Double momentum = metricSnapshotRepository
                .findFirstByInstrumentAndWindowStartBeforeOrderByWindowStartDesc(instrument, windowStart)
                .map(previous -> previous.getMentionCount() == 0
                        ? null
                        : ((counter.total() - previous.getMentionCount()) * 100.0) / previous.getMentionCount())
                .orElse(null);
        double net = counter.total() == 0 ? 0.0 : (counter.bullish - counter.bearish) / (double) counter.total();
        return new MetricSnapshot(
                instrument,
                windowStart,
                windowEnd,
                counter.total(),
                counter.bullish,
                counter.bearish,
                counter.neutral,
                net,
                momentum
        );
    }

    private static Instant floorToWindow(Instant instant) {
        long epoch = instant.getEpochSecond();
        long windowSeconds = WINDOW.toSeconds();
        return Instant.ofEpochSecond(epoch - (epoch % windowSeconds));
    }

    private static final class Counter {
        private int bullish;
        private int bearish;
        private int neutral;

        void add(SentimentLabel label) {
            switch (label) {
                case BULLISH -> bullish++;
                case BEARISH -> bearish++;
                case NEUTRAL -> neutral++;
            }
        }

        int total() {
            return bullish + bearish + neutral;
        }
    }
}

