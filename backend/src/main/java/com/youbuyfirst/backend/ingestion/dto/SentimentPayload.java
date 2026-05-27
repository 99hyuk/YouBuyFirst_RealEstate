package com.youbuyfirst.backend.ingestion.dto;

import com.youbuyfirst.backend.sentiment.SentimentLabel;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record SentimentPayload(
        Long instrumentId,
        @NotBlank String market,
        @NotBlank String symbol,
        @NotNull SentimentLabel sentiment,
        @DecimalMin("0.0") @DecimalMax("1.0") double confidence,
        String rationale,
        String model
) {
    public SentimentPayload(
            String market,
            String symbol,
            SentimentLabel sentiment,
            double confidence,
            String rationale,
            String model
    ) {
        this(null, market, symbol, sentiment, confidence, rationale, model);
    }
}
