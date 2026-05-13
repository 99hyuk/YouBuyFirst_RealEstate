package com.youbuyfirst.backend.ingestion.dto;

public record IngestionResponse(
        String source,
        String runId,
        int seenPosts,
        int acceptedPosts,
        int duplicatePosts
) {
}

