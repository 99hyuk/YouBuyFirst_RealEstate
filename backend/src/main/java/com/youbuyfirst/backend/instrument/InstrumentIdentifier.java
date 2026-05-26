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
import java.util.Locale;

@Entity
@Table(
        name = "instrument_identifiers",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_instrument_identifier_namespace_value_purpose",
                columnNames = {"namespace", "normalized_identifier", "purpose"}
        )
)
public class InstrumentIdentifier {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "instrument_id", nullable = false)
    private Instrument instrument;

    @Column(nullable = false, length = 80)
    private String namespace;

    @Column(nullable = false, length = 160)
    private String identifier;

    @Column(name = "normalized_identifier", nullable = false, length = 160)
    private String normalizedIdentifier;

    @Column(nullable = false, length = 60)
    private String purpose;

    @Column(nullable = false, length = 80)
    private String source;

    @Column(nullable = false)
    private Boolean enabled;

    @Column(length = 500)
    private String notes;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected InstrumentIdentifier() {
    }

    public InstrumentIdentifier(
            Instrument instrument,
            String namespace,
            String identifier,
            String purpose,
            String source,
            Boolean enabled,
            String notes,
            Instant createdAt
    ) {
        this.instrument = instrument;
        this.namespace = normalizeToken(namespace);
        this.identifier = identifier;
        this.normalizedIdentifier = normalizeIdentifier(identifier);
        this.purpose = normalizeToken(purpose);
        this.source = source;
        this.enabled = enabled;
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

    public String getNamespace() {
        return namespace;
    }

    public String getIdentifier() {
        return identifier;
    }

    public String getNormalizedIdentifier() {
        return normalizedIdentifier;
    }

    public String getPurpose() {
        return purpose;
    }

    public String getSource() {
        return source;
    }

    public Boolean getEnabled() {
        return enabled;
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

    private static String normalizeToken(String value) {
        return value == null ? "" : value.trim().toUpperCase(Locale.ROOT);
    }

    public static String normalizeIdentifier(String value) {
        return value == null ? "" : value.trim().toUpperCase(Locale.ROOT).replace(" ", "");
    }
}
