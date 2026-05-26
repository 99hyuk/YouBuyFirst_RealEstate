package com.youbuyfirst.backend.market;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(
        name = "quote_snapshots",
        uniqueConstraints = @UniqueConstraint(name = "uk_quote_snapshots_symbol", columnNames = "symbol")
)
public class QuoteSnapshot {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "instrument_id")
    private Long instrumentId;

    @Column(nullable = false, length = 40)
    private String symbol;

    @Column(nullable = false, length = 200)
    private String name;

    @Column(nullable = false, length = 20)
    private String market;

    @Column(nullable = false, length = 10)
    private String currency;

    @Column(nullable = false, precision = 19, scale = 6)
    private BigDecimal price;

    @Column(name = "change_amount", nullable = false, precision = 19, scale = 6)
    private BigDecimal change;

    @Column(name = "change_pct", nullable = false, precision = 12, scale = 4)
    private BigDecimal changePct;

    @Column(nullable = false)
    private long volume;

    @Column(name = "as_of", nullable = false)
    private Instant asOf;

    @Column(nullable = false, length = 100)
    private String provider;

    @Column(name = "delay_label", nullable = false, length = 120)
    private String delayLabel;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(name = "collected_at", nullable = false)
    private Instant collectedAt;

    protected QuoteSnapshot() {
    }

    public QuoteSnapshot(String symbol) {
        this(null, symbol);
    }

    public QuoteSnapshot(Long instrumentId, String symbol) {
        this.instrumentId = instrumentId;
        this.symbol = symbol;
    }

    public void update(
            Long instrumentId,
            String name,
            String market,
            String currency,
            BigDecimal price,
            BigDecimal change,
            BigDecimal changePct,
            long volume,
            Instant asOf,
            String provider,
            String delayLabel,
            String dataStatus,
            Instant collectedAt
    ) {
        this.instrumentId = instrumentId;
        this.name = name;
        this.market = market;
        this.currency = currency;
        this.price = price;
        this.change = change;
        this.changePct = changePct;
        this.volume = volume;
        this.asOf = asOf;
        this.provider = provider;
        this.delayLabel = delayLabel;
        this.dataStatus = dataStatus;
        this.collectedAt = collectedAt;
    }

    public Long getInstrumentId() {
        return instrumentId;
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

    public BigDecimal getPrice() {
        return price;
    }

    public BigDecimal getChange() {
        return change;
    }

    public BigDecimal getChangePct() {
        return changePct;
    }

    public long getVolume() {
        return volume;
    }

    public Instant getAsOf() {
        return asOf;
    }

    public String getProvider() {
        return provider;
    }

    public String getDelayLabel() {
        return delayLabel;
    }

    public String getDataStatus() {
        return dataStatus;
    }
}
