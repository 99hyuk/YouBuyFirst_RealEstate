package com.youbuyfirst.backend.market;

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

import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(
        name = "chart_candles",
        uniqueConstraints = @UniqueConstraint(name = "uk_chart_candles_set_date", columnNames = {"set_id", "trade_date"})
)
public class ChartCandle {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "set_id", nullable = false)
    private ChartCandleSet candleSet;

    @Column(name = "trade_date", nullable = false)
    private LocalDate tradeDate;

    @Column(name = "open_price", nullable = false, precision = 19, scale = 6)
    private BigDecimal open;

    @Column(name = "high_price", nullable = false, precision = 19, scale = 6)
    private BigDecimal high;

    @Column(name = "low_price", nullable = false, precision = 19, scale = 6)
    private BigDecimal low;

    @Column(name = "close_price", nullable = false, precision = 19, scale = 6)
    private BigDecimal close;

    @Column(nullable = false)
    private long volume;

    protected ChartCandle() {
    }

    public ChartCandle(
            ChartCandleSet candleSet,
            LocalDate tradeDate,
            BigDecimal open,
            BigDecimal high,
            BigDecimal low,
            BigDecimal close,
            long volume
    ) {
        this.candleSet = candleSet;
        this.tradeDate = tradeDate;
        this.open = open;
        this.high = high;
        this.low = low;
        this.close = close;
        this.volume = volume;
    }

    public LocalDate getTradeDate() {
        return tradeDate;
    }

    public BigDecimal getOpen() {
        return open;
    }

    public BigDecimal getHigh() {
        return high;
    }

    public BigDecimal getLow() {
        return low;
    }

    public BigDecimal getClose() {
        return close;
    }

    public long getVolume() {
        return volume;
    }
}
