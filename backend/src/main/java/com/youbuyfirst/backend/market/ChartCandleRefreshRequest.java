package com.youbuyfirst.backend.market;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

import java.time.Duration;
import java.time.Instant;

@Entity
@Table(
        name = "chart_candle_refresh_requests",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_chart_candle_refresh_requests_symbol_range_interval",
                columnNames = {"symbol", "range_label", "candle_interval"}
        )
)
public class ChartCandleRefreshRequest {

    public static final String STATUS_PENDING = "PENDING";
    public static final String STATUS_IN_PROGRESS = "IN_PROGRESS";
    public static final String STATUS_SUCCESS = "SUCCESS";
    public static final String STATUS_FAILED = "FAILED";

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 40)
    private String symbol;

    @Column(name = "range_label", nullable = false, length = 10)
    private String rangeLabel;

    @Column(name = "candle_interval", nullable = false, length = 10)
    private String candleInterval;

    @Column(nullable = false, length = 30)
    private String status;

    @Column(name = "requested_at", nullable = false)
    private Instant requestedAt;

    @Column(name = "last_attempt_at")
    private Instant lastAttemptAt;

    @Column(name = "completed_at")
    private Instant completedAt;

    @Column(name = "error_message", length = 500)
    private String errorMessage;

    protected ChartCandleRefreshRequest() {
    }

    public ChartCandleRefreshRequest(String symbol, String rangeLabel, String candleInterval, Instant now) {
        this.symbol = symbol;
        this.rangeLabel = rangeLabel;
        this.candleInterval = candleInterval;
        requestAgain(now);
    }

    public void requestAgain(Instant now) {
        this.status = STATUS_PENDING;
        this.requestedAt = now;
        this.lastAttemptAt = null;
        this.completedAt = null;
        this.errorMessage = null;
    }

    public void claim(Instant now) {
        this.status = STATUS_IN_PROGRESS;
        this.lastAttemptAt = now;
        this.completedAt = null;
        this.errorMessage = null;
    }

    public void complete(Instant now) {
        this.status = STATUS_SUCCESS;
        this.completedAt = now;
        this.errorMessage = null;
    }

    public void fail(Instant now, String message) {
        this.status = STATUS_FAILED;
        this.lastAttemptAt = now;
        this.errorMessage = message == null || message.isBlank()
                ? "chart candle refresh failed"
                : message.substring(0, Math.min(message.length(), 500));
    }

    public String getSymbol() {
        return symbol;
    }

    public String getRangeLabel() {
        return rangeLabel;
    }

    public String getCandleInterval() {
        return candleInterval;
    }

    public String getStatus() {
        return status;
    }

    public boolean isActiveInProgress(Instant now, Duration leaseDuration) {
        return STATUS_IN_PROGRESS.equals(status)
                && lastAttemptAt != null
                && lastAttemptAt.isAfter(now.minus(leaseDuration));
    }
}
