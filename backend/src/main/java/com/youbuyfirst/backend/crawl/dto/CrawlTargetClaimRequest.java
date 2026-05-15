package com.youbuyfirst.backend.crawl.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

import java.util.List;

public record CrawlTargetClaimRequest(
        @NotBlank String workerId,
        String runtimeEnvironment,
        List<String> allowedSources,
        @Min(1) @Max(100) Integer limit
) {
    public int normalizedLimit() {
        if (limit == null) {
            return 20;
        }
        return Math.max(1, Math.min(limit, 100));
    }
}
