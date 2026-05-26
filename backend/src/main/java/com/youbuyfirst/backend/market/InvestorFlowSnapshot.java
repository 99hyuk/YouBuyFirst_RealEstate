package com.youbuyfirst.backend.market;

import com.youbuyfirst.backend.market.dto.InvestorFlowLegRequest;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(
        name = "investor_flow_snapshots",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_investor_flow_snapshots_symbol_trade_date",
                columnNames = {"symbol", "trade_date"}
        )
)
public class InvestorFlowSnapshot {

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

    @Column(name = "trade_date", nullable = false)
    private LocalDate tradeDate;

    @Column(nullable = false, length = 100)
    private String provider;

    @Column(name = "source_label", nullable = false, length = 200)
    private String sourceLabel;

    @Column(name = "delay_label", nullable = false, length = 120)
    private String delayLabel;

    @Column(name = "as_of", nullable = false)
    private Instant asOf;

    @Column(name = "data_status", nullable = false, length = 30)
    private String dataStatus;

    @Column(name = "collected_at", nullable = false)
    private Instant collectedAt;

    @Column(name = "individual_net_amount", precision = 19, scale = 2)
    private BigDecimal individualNetAmount;

    @Column(name = "individual_net_volume", nullable = false)
    private long individualNetVolume;

    @Column(name = "individual_derived", nullable = false)
    private boolean individualDerived;

    @Column(name = "foreign_net_amount", precision = 19, scale = 2)
    private BigDecimal foreignNetAmount;

    @Column(name = "foreign_net_volume", nullable = false)
    private long foreignNetVolume;

    @Column(name = "foreign_derived", nullable = false)
    private boolean foreignDerived;

    @Column(name = "institution_net_amount", precision = 19, scale = 2)
    private BigDecimal institutionNetAmount;

    @Column(name = "institution_net_volume", nullable = false)
    private long institutionNetVolume;

    @Column(name = "institution_derived", nullable = false)
    private boolean institutionDerived;

    protected InvestorFlowSnapshot() {
    }

    public InvestorFlowSnapshot(String symbol) {
        this(null, symbol);
    }

    public InvestorFlowSnapshot(Long instrumentId, String symbol) {
        this.instrumentId = instrumentId;
        this.symbol = symbol;
    }

    public void update(
            Long instrumentId,
            String name,
            String market,
            String currency,
            LocalDate tradeDate,
            String provider,
            String sourceLabel,
            String delayLabel,
            Instant asOf,
            String dataStatus,
            Instant collectedAt,
            InvestorFlowLegRequest individual,
            InvestorFlowLegRequest foreign,
            InvestorFlowLegRequest institution
    ) {
        this.instrumentId = instrumentId;
        this.name = name;
        this.market = market;
        this.currency = currency;
        this.tradeDate = tradeDate;
        this.provider = provider;
        this.sourceLabel = sourceLabel;
        this.delayLabel = delayLabel;
        this.asOf = asOf;
        this.dataStatus = dataStatus;
        this.collectedAt = collectedAt;
        this.individualNetAmount = individual.netAmount();
        this.individualNetVolume = individual.netVolume();
        this.individualDerived = Boolean.TRUE.equals(individual.derived());
        this.foreignNetAmount = foreign.netAmount();
        this.foreignNetVolume = foreign.netVolume();
        this.foreignDerived = Boolean.TRUE.equals(foreign.derived());
        this.institutionNetAmount = institution.netAmount();
        this.institutionNetVolume = institution.netVolume();
        this.institutionDerived = Boolean.TRUE.equals(institution.derived());
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

    public LocalDate getTradeDate() {
        return tradeDate;
    }

    public String getProvider() {
        return provider;
    }

    public String getSourceLabel() {
        return sourceLabel;
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

    public BigDecimal getIndividualNetAmount() {
        return individualNetAmount;
    }

    public long getIndividualNetVolume() {
        return individualNetVolume;
    }

    public boolean isIndividualDerived() {
        return individualDerived;
    }

    public BigDecimal getForeignNetAmount() {
        return foreignNetAmount;
    }

    public long getForeignNetVolume() {
        return foreignNetVolume;
    }

    public boolean isForeignDerived() {
        return foreignDerived;
    }

    public BigDecimal getInstitutionNetAmount() {
        return institutionNetAmount;
    }

    public long getInstitutionNetVolume() {
        return institutionNetVolume;
    }

    public boolean isInstitutionDerived() {
        return institutionDerived;
    }
}
