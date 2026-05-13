package com.humanindicator.backend.instrument;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

@Entity
@Table(
        name = "instruments",
        uniqueConstraints = @UniqueConstraint(name = "uk_instrument_market_symbol", columnNames = {"market", "symbol"})
)
public class Instrument {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 20)
    private String market;

    @Column(nullable = false, length = 40)
    private String symbol;

    @Column(name = "name_ko", nullable = false, length = 200)
    private String nameKo;

    @Column(name = "name_en", length = 200)
    private String nameEn;

    @Column(nullable = false, length = 40)
    private String type;

    protected Instrument() {
    }

    public Instrument(String market, String symbol, String nameKo, String nameEn, String type) {
        this.market = market;
        this.symbol = symbol;
        this.nameKo = nameKo;
        this.nameEn = nameEn;
        this.type = type;
    }

    public Long getId() {
        return id;
    }

    public String getMarket() {
        return market;
    }

    public String getSymbol() {
        return symbol;
    }

    public String getNameKo() {
        return nameKo;
    }

    public String getNameEn() {
        return nameEn;
    }

    public String getType() {
        return type;
    }
}

