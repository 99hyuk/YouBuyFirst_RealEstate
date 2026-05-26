package com.youbuyfirst.backend.instrument;

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

    @Column(name = "normalized_alias", nullable = false, length = 200)
    private String normalizedAlias;

    @Column(nullable = false, length = 80)
    private String source;

    @Column(nullable = false)
    private Double confidence;

    @Column(nullable = false, length = 40)
    private String status;

    @Column(nullable = false)
    private Boolean ambiguous;

    @Column(length = 500)
    private String notes;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected InstrumentAlias() {
    }

    public InstrumentAlias(Instrument instrument, String alias) {
        this.instrument = instrument;
        this.alias = alias;
        this.normalizedAlias = normalizeAlias(alias);
        this.source = "seed";
        this.confidence = 1.0;
        this.status = "ACCEPTED";
        this.ambiguous = false;
        this.createdAt = Instant.now();
        this.updatedAt = this.createdAt;
    }

    public InstrumentAlias(
            Instrument instrument,
            String alias,
            String source,
            Double confidence,
            String status,
            Boolean ambiguous,
            String notes,
            Instant createdAt
    ) {
        this.instrument = instrument;
        this.alias = alias;
        this.normalizedAlias = normalizeAlias(alias);
        this.source = source;
        this.confidence = confidence;
        this.status = status;
        this.ambiguous = ambiguous;
        this.notes = notes;
        this.createdAt = createdAt;
        this.updatedAt = createdAt;
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

    public String getNormalizedAlias() {
        return normalizedAlias;
    }

    public String getSource() {
        return source;
    }

    public Double getConfidence() {
        return confidence;
    }

    public String getStatus() {
        return status;
    }

    public Boolean getAmbiguous() {
        return ambiguous;
    }

    public String getNotes() {
        return notes;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    private static String normalizeAlias(String value) {
        return value == null ? "" : value.trim().toUpperCase();
    }
}
