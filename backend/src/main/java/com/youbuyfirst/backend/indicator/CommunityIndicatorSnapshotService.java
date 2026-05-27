package com.youbuyfirst.backend.indicator;

import com.youbuyfirst.backend.indicator.CommunityIndicatorSnapshotResponse.KeywordCount;
import com.youbuyfirst.backend.indicator.CommunityIndicatorSnapshotResponse.Freshness;
import com.youbuyfirst.backend.indicator.CommunityIndicatorSnapshotResponse.Mood;
import com.youbuyfirst.backend.indicator.CommunityIndicatorSnapshotResponse.SourceMood;
import com.youbuyfirst.backend.indicator.CommunityIndicatorSnapshotResponse.StockMentionCount;
import com.youbuyfirst.backend.instrument.Instrument;
import com.youbuyfirst.backend.post.CommunityPost;
import com.youbuyfirst.backend.post.CommunityPostRepository;
import com.youbuyfirst.backend.post.PostMention;
import com.youbuyfirst.backend.post.PostMentionRepository;
import com.youbuyfirst.backend.sentiment.SentimentAnalysis;
import com.youbuyfirst.backend.sentiment.SentimentAnalysisRepository;
import com.youbuyfirst.backend.sentiment.SentimentLabel;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class CommunityIndicatorSnapshotService {

    private static final int KEYWORD_LIMIT = 10;
    private static final Pattern KEYWORD_PATTERN = Pattern.compile("[\\p{L}\\p{N}][\\p{L}\\p{N}._-]{1,}");
    private static final List<String> STOP_WORDS = List.of(
            "and", "the", "for", "with", "this", "that", "from", "today", "stock", "stocks",
            "post", "board", "market", "price", "share", "shares", "buy", "sell"
    );
    private static final String FRESHNESS_SOURCE = "community_posts/post_mentions/sentiment_analyses";

    private final CommunityPostRepository postRepository;
    private final PostMentionRepository mentionRepository;
    private final SentimentAnalysisRepository sentimentRepository;

    public CommunityIndicatorSnapshotService(
            CommunityPostRepository postRepository,
            PostMentionRepository mentionRepository,
            SentimentAnalysisRepository sentimentRepository
    ) {
        this.postRepository = postRepository;
        this.mentionRepository = mentionRepository;
        this.sentimentRepository = sentimentRepository;
    }

    @Transactional(readOnly = true)
    public CommunityIndicatorSnapshotResponse snapshot(Instant windowStart, int windowMinutes) {
        Duration window = Duration.ofMinutes(windowMinutes);
        Instant windowEnd = windowStart.plus(window);
        List<CommunityPost> posts = postRepository.findByPublishedAtGreaterThanEqualAndPublishedAtLessThan(windowStart, windowEnd);
        List<PostMention> mentions = mentionRepository.findMentionsInWindow(windowStart, windowEnd);
        List<SentimentAnalysis> sentiments = sentimentRepository.findAnalysesInWindow(windowStart, windowEnd);

        Counter market = new Counter();
        Map<SourceKey, SourceAccumulator> sources = new LinkedHashMap<>();
        Map<Long, StockAccumulator> stocks = new LinkedHashMap<>();
        Map<Long, CommunityPost> postsById = new LinkedHashMap<>();
        for (CommunityPost post : posts) {
            postsById.put(post.getId(), post);
        }

        for (PostMention mention : mentions) {
            CommunityPost post = mention.getPost();
            Instrument instrument = mention.getInstrument();
            SourceAccumulator source = sourceAccumulator(sources, post);
            StockAccumulator stock = stockAccumulator(stocks, instrument);
            market.mentionCount++;
            source.counter.mentionCount++;
            stock.counter.mentionCount++;
            stock.posts.put(post.getId(), post);
        }

        for (SentimentAnalysis sentiment : sentiments) {
            CommunityPost post = sentiment.getPost();
            Instrument instrument = sentiment.getInstrument();
            market.add(sentiment.getSentiment());
            sourceAccumulator(sources, post).counter.add(sentiment.getSentiment());
            StockAccumulator stock = stockAccumulator(stocks, instrument);
            stock.counter.add(sentiment.getSentiment());
            stock.posts.put(post.getId(), post);
        }

        return new CommunityIndicatorSnapshotResponse(
                windowStart,
                windowEnd,
                windowMinutes,
                freshness(posts, sentiments, windowEnd),
                market.toMood(),
                sources.values().stream()
                        .sorted(Comparator
                                .comparingInt((SourceAccumulator source) -> source.counter.mentionCount).reversed()
                                .thenComparing(source -> source.key.source())
                                .thenComparing(source -> source.key.boardId() == null ? "" : source.key.boardId()))
                        .map(source -> new SourceMood(
                                source.key.source(),
                                source.key.boardId(),
                                source.counter.mentionCount,
                                source.counter.bullishCount,
                                source.counter.bearishCount,
                                source.counter.neutralCount,
                                source.counter.netSentiment(),
                                topKeywords(postsForSource(posts, source.key))
                        ))
                        .toList(),
                stocks.values().stream()
                        .sorted(Comparator
                                .comparingInt((StockAccumulator stock) -> stock.counter.mentionCount).reversed()
                                .thenComparing(stock -> stock.instrument.getMarket())
                                .thenComparing(stock -> stock.instrument.getSymbol()))
                        .map(stock -> new StockMentionCount(
                                stock.instrument.getId(),
                                stock.instrument.getMarket(),
                                stock.instrument.getSymbol(),
                                displayName(stock.instrument),
                                stock.counter.mentionCount,
                                stock.counter.bullishCount,
                                stock.counter.bearishCount,
                                stock.counter.neutralCount,
                                stock.counter.netSentiment(),
                                topKeywords(new ArrayList<>(stock.posts.values()))
                        ))
                        .toList(),
                topKeywords(new ArrayList<>(postsById.values()))
        );
    }

    private static Freshness freshness(List<CommunityPost> posts, List<SentimentAnalysis> sentiments, Instant windowEnd) {
        Instant latestPublishedAt = null;
        Instant asOf = null;
        for (CommunityPost post : posts) {
            latestPublishedAt = max(latestPublishedAt, post.getPublishedAt());
            asOf = max(asOf, post.getCrawledAt());
        }
        for (SentimentAnalysis sentiment : sentiments) {
            asOf = max(asOf, sentiment.getAnalyzedAt());
        }

        boolean stale = asOf == null || asOf.isBefore(windowEnd);
        String staleReason = null;
        if (asOf == null) {
            staleReason = "no_source_data";
        } else if (stale) {
            staleReason = "source_as_of_before_window_end";
        }
        return new Freshness(FRESHNESS_SOURCE, asOf, latestPublishedAt, stale, staleReason);
    }

    private static Instant max(Instant current, Instant candidate) {
        if (candidate == null) {
            return current;
        }
        if (current == null || candidate.isAfter(current)) {
            return candidate;
        }
        return current;
    }

    private static SourceAccumulator sourceAccumulator(Map<SourceKey, SourceAccumulator> sources, CommunityPost post) {
        SourceKey key = new SourceKey(post.getSource(), post.getBoardId());
        return sources.computeIfAbsent(key, SourceAccumulator::new);
    }

    private static StockAccumulator stockAccumulator(Map<Long, StockAccumulator> stocks, Instrument instrument) {
        return stocks.computeIfAbsent(instrument.getId(), ignored -> new StockAccumulator(instrument));
    }

    private static List<CommunityPost> postsForSource(List<CommunityPost> posts, SourceKey key) {
        return posts.stream()
                .filter(post -> key.source().equals(post.getSource()))
                .filter(post -> key.boardId() == null ? post.getBoardId() == null : key.boardId().equals(post.getBoardId()))
                .toList();
    }

    private static List<KeywordCount> topKeywords(List<CommunityPost> posts) {
        Map<String, Integer> counts = new LinkedHashMap<>();
        for (CommunityPost post : posts) {
            countKeywords(post.getTitle(), counts);
            countKeywords(post.getContentSnippet(), counts);
        }
        return counts.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed().thenComparing(Map.Entry.comparingByKey()))
                .limit(KEYWORD_LIMIT)
                .map(entry -> new KeywordCount(entry.getKey(), entry.getValue()))
                .toList();
    }

    private static void countKeywords(String text, Map<String, Integer> counts) {
        if (text == null || text.isBlank()) {
            return;
        }
        Matcher matcher = KEYWORD_PATTERN.matcher(text);
        while (matcher.find()) {
            String keyword = matcher.group().toLowerCase(Locale.ROOT);
            if (keyword.length() < 2 || STOP_WORDS.contains(keyword)) {
                continue;
            }
            counts.merge(keyword, 1, Integer::sum);
        }
    }

    private static String displayName(Instrument instrument) {
        if (instrument.getNameKo() != null && !instrument.getNameKo().isBlank()) {
            return instrument.getNameKo();
        }
        if (instrument.getNameEn() != null && !instrument.getNameEn().isBlank()) {
            return instrument.getNameEn();
        }
        return instrument.getSymbol();
    }

    private record SourceKey(String source, String boardId) {
    }

    private static final class SourceAccumulator {
        private final SourceKey key;
        private final Counter counter = new Counter();

        private SourceAccumulator(SourceKey key) {
            this.key = key;
        }
    }

    private static final class StockAccumulator {
        private final Instrument instrument;
        private final Counter counter = new Counter();
        private final Map<Long, CommunityPost> posts = new LinkedHashMap<>();

        private StockAccumulator(Instrument instrument) {
            this.instrument = instrument;
        }
    }

    private static final class Counter {
        private int mentionCount;
        private int bullishCount;
        private int bearishCount;
        private int neutralCount;

        private void add(SentimentLabel label) {
            switch (label) {
                case BULLISH -> bullishCount++;
                case BEARISH -> bearishCount++;
                case NEUTRAL -> neutralCount++;
            }
        }

        private Mood toMood() {
            return new Mood(mentionCount, bullishCount, bearishCount, neutralCount, netSentiment());
        }

        private double netSentiment() {
            int total = bullishCount + bearishCount + neutralCount;
            if (total == 0) {
                return 0.0;
            }
            return (bullishCount - bearishCount) / (double) total;
        }
    }
}
