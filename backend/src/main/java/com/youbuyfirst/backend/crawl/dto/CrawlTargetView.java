package com.youbuyfirst.backend.crawl.dto;

import com.youbuyfirst.backend.crawl.CrawlTarget;
import com.youbuyfirst.backend.crawl.CrawlTargetStatus;

import java.time.Instant;

public record CrawlTargetView(
        String source,
        String targetId,
        String targetKind,
        CrawlTargetStatus status,
        String market,
        String symbol,
        String url,
        String label,
        int priority,
        int crawlIntervalSeconds,
        Instant nextAttemptAt,
        Instant lastAttemptAt,
        Instant lastSuccessAt,
        String lastStatus,
        int consecutiveFailures,
        String backoffCategory,
        Instant backoffUntil,
        String backoffReason
) {
    public static CrawlTargetView from(CrawlTarget target) {
        return new CrawlTargetView(
                target.getSource(),
                target.getTargetId(),
                target.getTargetKind(),
                target.getStatus(),
                target.getMarket(),
                target.getSymbol(),
                target.getUrl(),
                target.getLabel(),
                target.getPriority(),
                target.getCrawlIntervalSeconds(),
                target.getNextAttemptAt(),
                target.getLastAttemptAt(),
                target.getLastSuccessAt(),
                target.getLastStatus(),
                target.getConsecutiveFailures(),
                target.getBackoffCategory(),
                target.getBackoffUntil(),
                target.getBackoffReason()
        );
    }
}
