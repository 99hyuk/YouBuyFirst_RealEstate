package com.humanindicator.backend.metrics;

import com.humanindicator.backend.instrument.Instrument;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;

@Entity
@Table(
        name = "metric_snapshots",
        uniqueConstraints = @UniqueConstraint(name = "uk_metric_instrument_window", columnNames = {"instrument_id", "window_start"})
)
public class MetricSnapshot {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "instrument_id", nullable = false)
    private Instrument instrument;

    @Column(name = "window_start", nullable = false)
    private Instant windowStart;

    @Column(name = "window_end", nullable = false)
    private Instant windowEnd;

    @Column(name = "mention_count", nullable = false)
    private int mentionCount;

    @Column(name = "bullish_count", nullable = false)
    private int bullishCount;

    @Column(name = "bearish_count", nullable = false)
    private int bearishCount;

    @Column(name = "neutral_count", nullable = false)
    private int neutralCount;

    @Column(name = "net_sentiment", nullable = false)
    private double netSentiment;

    @Column(name = "momentum_percent")
    private Double momentumPercent;

    protected MetricSnapshot() {
    }

    public MetricSnapshot(Instrument instrument, Instant windowStart, Instant windowEnd, int mentionCount, int bullishCount, int bearishCount, int neutralCount, double netSentiment, Double momentumPercent) {
        this.instrument = instrument;
        this.windowStart = windowStart;
        this.windowEnd = windowEnd;
        this.mentionCount = mentionCount;
        this.bullishCount = bullishCount;
        this.bearishCount = bearishCount;
        this.neutralCount = neutralCount;
        this.netSentiment = netSentiment;
        this.momentumPercent = momentumPercent;
    }

    public Long getId() {
        return id;
    }

    public Instrument getInstrument() {
        return instrument;
    }

    public Instant getWindowStart() {
        return windowStart;
    }

    public Instant getWindowEnd() {
        return windowEnd;
    }

    public int getMentionCount() {
        return mentionCount;
    }

    public int getBullishCount() {
        return bullishCount;
    }

    public int getBearishCount() {
        return bearishCount;
    }

    public int getNeutralCount() {
        return neutralCount;
    }

    public double getNetSentiment() {
        return netSentiment;
    }

    public Double getMomentumPercent() {
        return momentumPercent;
    }
}

