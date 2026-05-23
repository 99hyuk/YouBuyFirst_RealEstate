package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.ChartCandleBarRequest;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

@Entity
@Table(
        name = "chart_candle_sets",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_chart_candle_sets_symbol_range_interval",
                columnNames = {"symbol", "range_label", "candle_interval"}
        )
)
public class ChartCandleSet {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 40)
    private String symbol;

    @Column(nullable = false, length = 200)
    private String name;

    @Column(nullable = false, length = 20)
    private String market;

    @Column(nullable = false, length = 10)
    private String currency;

    @Column(name = "range_label", nullable = false, length = 10)
    private String rangeLabel;

    @Column(name = "candle_interval", nullable = false, length = 10)
    private String candleInterval;

    @Column(nullable = false, length = 100)
    private String provider;

    @Column(name = "delay_label", nullable = false, length = 120)
    private String delayLabel;

    @Column(name = "as_of", nullable = false)
    private Instant asOf;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(name = "collected_at", nullable = false)
    private Instant collectedAt;

    @OneToMany(mappedBy = "candleSet", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("tradeDate ASC")
    private List<ChartCandle> bars = new ArrayList<>();

    protected ChartCandleSet() {
    }

    public ChartCandleSet(String symbol, String rangeLabel, String candleInterval) {
        this.symbol = symbol;
        this.rangeLabel = rangeLabel;
        this.candleInterval = candleInterval;
    }

    public void update(
            String name,
            String market,
            String currency,
            String provider,
            String delayLabel,
            Instant asOf,
            String dataStatus,
            Instant collectedAt,
            List<ChartCandleBarRequest> newBars
    ) {
        this.name = name;
        this.market = market;
        this.currency = currency;
        this.provider = provider;
        this.delayLabel = delayLabel;
        this.asOf = asOf;
        this.dataStatus = dataStatus;
        this.collectedAt = collectedAt;
        this.bars.clear();
        newBars.stream()
                .sorted(Comparator.comparing(ChartCandleBarRequest::date))
                .map(bar -> new ChartCandle(
                        this,
                        bar.date(),
                        bar.open(),
                        bar.high(),
                        bar.low(),
                        bar.close(),
                        bar.volume()
                ))
                .forEach(this.bars::add);
    }

    public void clearBars() {
        this.bars.clear();
    }

    public String getSymbol() {
        return symbol;
    }

    public String getName() {
        return name;
    }

    public String getMarket() {
        return market;
    }

    public String getCurrency() {
        return currency;
    }

    public String getRangeLabel() {
        return rangeLabel;
    }

    public String getCandleInterval() {
        return candleInterval;
    }

    public String getProvider() {
        return provider;
    }

    public String getDelayLabel() {
        return delayLabel;
    }

    public Instant getAsOf() {
        return asOf;
    }

    public String getDataStatus() {
        return dataStatus;
    }

    public List<ChartCandle> getBars() {
        return bars;
    }
}
