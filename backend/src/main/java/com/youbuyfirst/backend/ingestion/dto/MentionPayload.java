package com.youbuyfirst.backend.ingestion.dto;

import jakarta.validation.constraints.NotBlank;

public record MentionPayload(
        Long instrumentId,
        @NotBlank String market,
        @NotBlank String symbol,
        @NotBlank String matchedText
) {
    public MentionPayload(String market, String symbol, String matchedText) {
        this(null, market, symbol, matchedText);
    }
}
