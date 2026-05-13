package com.humanindicator.backend.ingestion.dto;

import jakarta.validation.constraints.NotBlank;

public record MentionPayload(
        @NotBlank String market,
        @NotBlank String symbol,
        @NotBlank String matchedText
) {
}

