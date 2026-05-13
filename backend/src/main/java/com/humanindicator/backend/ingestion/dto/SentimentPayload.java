package com.humanindicator.backend.ingestion.dto;

import com.humanindicator.backend.sentiment.SentimentLabel;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record SentimentPayload(
        @NotBlank String market,
        @NotBlank String symbol,
        @NotNull SentimentLabel sentiment,
        @DecimalMin("0.0") @DecimalMax("1.0") double confidence,
        String rationale,
        String model
) {
}

