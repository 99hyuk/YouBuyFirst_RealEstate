package com.youbuyfirst.backend.instrument;

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

    @Column(name = "exchange_code", length = 40)
    private String exchangeCode;

    protected Instrument() {
    }

    public Instrument(String market, String symbol, String nameKo, String nameEn, String type) {
        this(market, symbol, nameKo, nameEn, type, null);
    }

    public Instrument(String market, String symbol, String nameKo, String nameEn, String type, String exchangeCode) {
        this.market = market;
        this.symbol = symbol;
        this.nameKo = nameKo;
        this.nameEn = nameEn;
        this.type = type;
        this.exchangeCode = exchangeCode;
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

    public String getExchangeCode() {
        return exchangeCode;
    }

    public boolean applySeed(String nameKo, String nameEn, String type, String exchangeCode) {
        boolean changed = false;
        if ("KR".equalsIgnoreCase(market) && hasText(nameKo) && !nameKo.equals(this.nameKo)) {
            this.nameKo = nameKo;
            changed = true;
        }
        if (!hasText(this.nameKo) && hasText(nameKo)) {
            this.nameKo = nameKo;
            changed = true;
        }
        if (hasText(nameEn) && !nameEn.equals(this.nameEn)) {
            this.nameEn = nameEn;
            changed = true;
        }
        if (hasText(type) && !type.equals(this.type)) {
            this.type = type;
            changed = true;
        }
        if (hasText(exchangeCode) && !exchangeCode.equals(this.exchangeCode)) {
            this.exchangeCode = exchangeCode;
            changed = true;
        }
        return changed;
    }

    private static boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
