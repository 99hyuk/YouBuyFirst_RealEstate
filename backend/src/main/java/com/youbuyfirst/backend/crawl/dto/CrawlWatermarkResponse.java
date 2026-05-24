package com.youbuyfirst.backend.crawl.dto;

import java.time.Instant;

public record CrawlWatermarkResponse(
        String source,
        String boardId,
        String lastSeenExternalId,
        Instant lastSeenPublishedAt
) {
}
