package com.humanindicator.backend.ingestion.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import org.hibernate.validator.constraints.URL;

import java.time.Instant;
import java.util.List;

public record PostPayload(
        @NotBlank String externalId,
        @NotBlank @URL String url,
        @NotBlank String title,
        String contentSnippet,
        String authorDisplayName,
        @NotNull Instant publishedAt,
        List<@Valid MentionPayload> mentions,
        List<@Valid SentimentPayload> sentiments
) {
}

