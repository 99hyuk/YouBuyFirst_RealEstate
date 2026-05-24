package com.youbuyfirst.backend.ingestion.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
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
        String boardId,
        @Min(0) Integer viewCount,
        @Min(0) Integer recommendCount,
        @Min(0) Integer commentCount,
        List<@Valid MentionPayload> mentions,
        List<@Valid SentimentPayload> sentiments
) {
    public PostPayload(
            String externalId,
            String url,
            String title,
            String contentSnippet,
            String authorDisplayName,
            Instant publishedAt,
            List<@Valid MentionPayload> mentions,
            List<@Valid SentimentPayload> sentiments
    ) {
        this(externalId, url, title, contentSnippet, authorDisplayName, publishedAt, null, null, null, null, mentions, sentiments);
    }
}
