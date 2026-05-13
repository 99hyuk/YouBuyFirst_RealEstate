package com.humanindicator.backend.instrument;

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

@Entity
@Table(
        name = "instrument_aliases",
        uniqueConstraints = @UniqueConstraint(name = "uk_instrument_alias", columnNames = {"instrument_id", "alias"})
)
public class InstrumentAlias {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "instrument_id", nullable = false)
    private Instrument instrument;

    @Column(nullable = false, length = 200)
    private String alias;

    protected InstrumentAlias() {
    }

    public InstrumentAlias(Instrument instrument, String alias) {
        this.instrument = instrument;
        this.alias = alias;
    }

    public Long getId() {
        return id;
    }

    public Instrument getInstrument() {
        return instrument;
    }

    public String getAlias() {
        return alias;
    }
}

