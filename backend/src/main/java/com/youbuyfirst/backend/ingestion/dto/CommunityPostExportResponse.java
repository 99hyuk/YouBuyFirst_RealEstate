package com.youbuyfirst.backend.ingestion.dto;

import java.time.Instant;
import java.util.List;

public record CommunityPostExportResponse(
        String source,
        Instant publishedFrom,
        Instant publishedTo,
        int limit,
        List<CommunityPostExportItemResponse> items
) {
}
