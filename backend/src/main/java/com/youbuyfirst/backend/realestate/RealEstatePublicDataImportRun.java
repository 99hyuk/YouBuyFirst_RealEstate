package com.youbuyfirst.backend.realestate;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(
        name = "real_estate_public_data_import_runs",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_real_estate_public_data_import_runs_run_key",
                columnNames = "run_key"
        )
)
public class RealEstatePublicDataImportRun {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "run_key", nullable = false, length = 180)
    private String runKey;

    @Column(name = "provider_dataset", nullable = false, length = 100)
    private String providerDataset;

    @Column(name = "run_type", nullable = false, length = 40)
    private String runType;

    @Column(name = "requested_from")
    private LocalDate requestedFrom;

    @Column(name = "requested_to")
    private LocalDate requestedTo;

    @Column(name = "request_params_json", nullable = false, columnDefinition = "text")
    private String requestParamsJson;

    @Column(nullable = false, length = 30)
    private String status;

    @Column(name = "rows_seen", nullable = false)
    private long rowsSeen;

    @Column(name = "rows_landed", nullable = false)
    private long rowsLanded;

    @Column(name = "rows_staged", nullable = false)
    private long rowsStaged;

    @Column(name = "rows_promoted", nullable = false)
    private long rowsPromoted;

    @Column(name = "started_at", nullable = false)
    private Instant startedAt;

    @Column(name = "finished_at")
    private Instant finishedAt;

    @Column(name = "error_message", columnDefinition = "text")
    private String errorMessage;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    protected RealEstatePublicDataImportRun() {
    }

    public RealEstatePublicDataImportRun(String runKey) {
        this.runKey = runKey;
    }

    public void update(
            String providerDataset,
            String runType,
            LocalDate requestedFrom,
            LocalDate requestedTo,
            String requestParamsJson,
            String status,
            long rowsSeen,
            long rowsLanded,
            long rowsStaged,
            Instant startedAt,
            Instant finishedAt,
            String errorMessage,
            Instant now
    ) {
        this.providerDataset = providerDataset;
        this.runType = runType;
        this.requestedFrom = requestedFrom;
        this.requestedTo = requestedTo;
        this.requestParamsJson = requestParamsJson;
        this.status = status;
        this.rowsSeen = rowsSeen;
        this.rowsLanded = rowsLanded;
        this.rowsStaged = rowsStaged;
        this.startedAt = startedAt;
        this.finishedAt = finishedAt;
        this.errorMessage = errorMessage;
        if (this.createdAt == null) {
            this.createdAt = now;
        }
        this.updatedAt = now;
    }

    public void markPromoted(long rowsPromoted, Instant now) {
        this.rowsPromoted = rowsPromoted;
        this.updatedAt = now;
    }

    public Long getId() {
        return id;
    }

    public String getRunKey() {
        return runKey;
    }

    public String getProviderDataset() {
        return providerDataset;
    }

    public String getRunType() {
        return runType;
    }

    public LocalDate getRequestedFrom() {
        return requestedFrom;
    }

    public LocalDate getRequestedTo() {
        return requestedTo;
    }

    public String getStatus() {
        return status;
    }

    public long getRowsSeen() {
        return rowsSeen;
    }

    public long getRowsLanded() {
        return rowsLanded;
    }

    public long getRowsStaged() {
        return rowsStaged;
    }

    public long getRowsPromoted() {
        return rowsPromoted;
    }

    public Instant getStartedAt() {
        return startedAt;
    }

    public Instant getFinishedAt() {
        return finishedAt;
    }

    public String getErrorMessage() {
        return errorMessage;
    }
}
