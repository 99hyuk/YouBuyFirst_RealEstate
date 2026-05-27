package com.youbuyfirst.backend.indicator;

import java.time.Instant;
import java.util.List;

public record CommunityIndicatorSnapshotResponse(
        Instant windowStart,
        Instant windowEnd,
        int windowMinutes,
        Freshness freshness,
        Mood marketMood,
        List<SourceMood> sourceMoods,
        List<StockMentionCount> stockMentionCounts,
        List<KeywordCount> topKeywords
) {
    public record Freshness(
            String source,
            Instant asOf,
            Instant latestPublishedAt,
            boolean stale,
            String staleReason
    ) {
    }

    public record Mood(
            int mentionCount,
            int bullishCount,
            int bearishCount,
            int neutralCount,
            double netSentiment
    ) {
    }

    public record SourceMood(
            String source,
            String boardId,
            int mentionCount,
            int bullishCount,
            int bearishCount,
            int neutralCount,
            double netSentiment,
            List<KeywordCount> topKeywords
    ) {
    }

    public record StockMentionCount(
            Long instrumentId,
            String market,
            String symbol,
            String name,
            int mentionCount,
            int bullishCount,
            int bearishCount,
            int neutralCount,
            double netSentiment,
            List<KeywordCount> topKeywords
    ) {
    }

    public record KeywordCount(String keyword, int count) {
    }
}
