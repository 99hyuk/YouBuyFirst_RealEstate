package com.youbuyfirst.backend.realestate.batch;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.realestate.dto.RealEstateContentItemRequest;
import org.springframework.stereotype.Component;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

import javax.xml.parsers.DocumentBuilderFactory;
import java.io.StringReader;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
public class NewsroomContentCollector {

    private static final ObjectMapper JSON = new ObjectMapper();
    private static final Pattern YOUTUBE_LENGTH_SECONDS =
            Pattern.compile("\\\"lengthSeconds\\\"\\s*:\\s*\\\"?(\\d+)\\\"?");
    private static final Pattern YOUTUBE_VIEW_COUNT =
            Pattern.compile("\\\"viewCount\\\"\\s*:\\s*\\\"?(\\d+)\\\"?");
    private static final Pattern YOUTUBE_KEYWORDS =
            Pattern.compile("\\\"keywords\\\"\\s*:\\s*(\\[[^]]*])", Pattern.DOTALL);
    private static final Pattern HTML_META_KEYWORDS =
            Pattern.compile("<meta\\s+name=\\\"keywords\\\"\\s+content=\\\"([^\\\"]*)\\\"", Pattern.CASE_INSENSITIVE);

    private final NewsroomContentProperties properties;
    private final RealEstateExternalFetchClient fetchClient;

    public NewsroomContentCollector(
            NewsroomContentProperties properties,
            RealEstateExternalFetchClient fetchClient
    ) {
        this.properties = properties;
        this.fetchClient = fetchClient;
    }

    public List<RealEstateContentItemRequest> collect(Instant ingestedAt) {
        List<RealEstateContentItemRequest> items = new ArrayList<>();
        for (NewsroomContentProperties.Source source : properties.getSources()) {
            if (blank(source.getUrl())) {
                continue;
            }
            RealEstateExternalFetchResult result = fetchClient.fetch(source.getUrl());
            if (result == null || !result.success() || blank(result.body())) {
                continue;
            }
            items.addAll(parseFeed(source, result.body(), ingestedAt));
        }
        return items;
    }

    private List<RealEstateContentItemRequest> parseFeed(
            NewsroomContentProperties.Source source,
            String body,
            Instant ingestedAt
    ) {
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setExpandEntityReferences(false);
            try {
                factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            } catch (Exception ignored) {
                // Some XML parsers do not expose this feature; entity expansion is still disabled above.
            }
            Document document = factory.newDocumentBuilder().parse(new InputSource(new StringReader(body)));
            NodeList rssItems = document.getElementsByTagName("item");
            if (rssItems.getLength() > 0) {
                return parseRssItems(source, rssItems, ingestedAt);
            }
            return parseAtomEntries(source, document.getElementsByTagName("entry"), ingestedAt);
        } catch (Exception ignored) {
            return List.of();
        }
    }

    private List<RealEstateContentItemRequest> parseRssItems(
            NewsroomContentProperties.Source source,
            NodeList nodes,
            Instant ingestedAt
    ) {
        List<RealEstateContentItemRequest> items = new ArrayList<>();
        for (int index = 0; index < nodes.getLength(); index++) {
            try {
                Element item = asElement(nodes.item(index));
                if (item == null) {
                    continue;
                }
                String title = trimTo(childText(item, "title"), 200);
                String url = trimTo(childText(item, "link"), 1000);
                if (blank(title) || blank(url)) {
                    continue;
                }
                String snippet = trimTo(stripHtml(childText(item, "description")), 1000);
                String effectiveDomain = firstNonBlank(domain(rssSourceUrl(item)), domain(url));
                Instant publishedAt = parseDate(childText(item, "pubDate"));
                if (!withinMaxAge(source, publishedAt, ingestedAt)) {
                    continue;
                }
            if (!matchesSourceFilters(source, title, snippet, url, effectiveDomain, null)) {
                    continue;
                }
                items.add(contentRequest(source, title, snippet, url, effectiveDomain, publishedAt, ingestedAt));
                if (reachedMaxItems(source, items)) {
                    break;
                }
            } catch (Exception ignored) {
                continue;
            }
        }
        return items;
    }

    private List<RealEstateContentItemRequest> parseAtomEntries(
            NewsroomContentProperties.Source source,
            NodeList nodes,
            Instant ingestedAt
    ) {
        List<RealEstateContentItemRequest> items = new ArrayList<>();
        for (int index = 0; index < nodes.getLength(); index++) {
            try {
                Element entry = asElement(nodes.item(index));
                if (entry == null) {
                    continue;
                }
                String title = trimTo(childText(entry, "title"), 200);
                String url = trimTo(atomLink(entry), 1000);
                if (blank(title) || blank(url)) {
                    continue;
                }
                String snippet = trimTo(stripHtml(firstNonBlank(
                        firstNonBlank(childText(entry, "summary"), childText(entry, "content")),
                        childText(entry, "media:description")
                )), 1000);
                String effectiveDomain = domain(url);
                Instant publishedAt = parseDate(firstNonBlank(childText(entry, "published"), childText(entry, "updated")));
                if (!withinMaxAge(source, publishedAt, ingestedAt)) {
                    continue;
                }
                if (!matchesSourceFilters(source, title, snippet, url, effectiveDomain, youtubeFeedViewCount(entry))) {
                    continue;
                }
                items.add(contentRequest(source, title, snippet, url, effectiveDomain, publishedAt, ingestedAt));
                if (reachedMaxItems(source, items)) {
                    break;
                }
            } catch (Exception ignored) {
                continue;
            }
        }
        return items;
    }

    private boolean matchesSourceFilters(
            NewsroomContentProperties.Source source,
            String title,
            String snippet,
            String url,
            String effectiveDomain,
            Long feedViewCount
    ) {
        if (!matchesAllowedDomain(source, effectiveDomain)) {
            return false;
        }
        List<String> excludedTerms = source.getExcludedTerms();
        String baseSearchable = String.join(" ", safe(title), safe(snippet), safe(url), safe(effectiveDomain))
                .toLowerCase(Locale.ROOT);
        if (containsAnyTerm(excludedTerms, baseSearchable)) {
            return false;
        }
        if (isVideoSource(source) && isYouTubeShortsUrl(url)) {
            return false;
        }
        VideoMetadata videoMetadata = videoMetadataFor(source, url, feedViewCount);
        if (!passesVideoQuality(source, videoMetadata)) {
            return false;
        }
        List<String> requiredTerms = source.getRequiredTerms();
        String searchable = String.join(" ", baseSearchable, videoMetadata.searchableText())
                .toLowerCase(Locale.ROOT);
        if (containsAnyTerm(excludedTerms, searchable)) {
            return false;
        }
        if (!matchesRequiredTerms(requiredTerms, searchable)) {
            return false;
        }
        if (!matchesRequiredTerms(source.getRequiredTopicTerms(), searchable)) {
            return false;
        }
        return true;
    }

    private static boolean matchesRequiredTerms(List<String> terms, String searchable) {
        if (terms == null || terms.isEmpty()) {
            return true;
        }
        for (String term : terms) {
            String normalized = firstNonBlank(term, null);
            if (normalized != null && searchable.contains(normalized.toLowerCase(Locale.ROOT))) {
                return true;
            }
        }
        return false;
    }

    private static boolean containsAnyTerm(List<String> terms, String searchable) {
        if (terms == null || terms.isEmpty()) {
            return false;
        }
        for (String term : terms) {
            String normalized = firstNonBlank(term, null);
            if (normalized != null && searchable.contains(normalized.toLowerCase(Locale.ROOT))) {
                return true;
            }
        }
        return false;
    }

    private static boolean matchesAllowedDomain(NewsroomContentProperties.Source source, String effectiveDomain) {
        List<String> allowedDomains = source.getAllowedDomains();
        if (allowedDomains == null || allowedDomains.isEmpty()) {
            return true;
        }
        String domain = firstNonBlank(effectiveDomain, null);
        if (domain == null) {
            return false;
        }
        for (String allowedDomain : allowedDomains) {
            if (domainMatches(domain, allowedDomain)) {
                return true;
            }
        }
        return false;
    }

    private static boolean domainMatches(String domain, String allowedDomain) {
        String normalizedDomain = domain.toLowerCase(Locale.ROOT);
        String normalizedAllowed = firstNonBlank(allowedDomain, "").toLowerCase(Locale.ROOT);
        if (normalizedAllowed.startsWith("www.")) {
            normalizedAllowed = normalizedAllowed.substring(4);
        }
        if (normalizedDomain.startsWith("www.")) {
            normalizedDomain = normalizedDomain.substring(4);
        }
        return normalizedDomain.equals(normalizedAllowed)
                || normalizedDomain.endsWith("." + normalizedAllowed);
    }

    private VideoMetadata videoMetadataFor(NewsroomContentProperties.Source source, String url, Long feedViewCount) {
        if (!isVideoSource(source)) {
            return VideoMetadata.empty();
        }
        RealEstateExternalFetchResult result = fetchClient.fetch(url);
        if (result == null || !result.success() || blank(result.body())) {
            return VideoMetadata.fromFeedViewCount(feedViewCount);
        }
        return parseYouTubeMetadata(result.body(), feedViewCount);
    }

    private static boolean passesVideoQuality(NewsroomContentProperties.Source source, VideoMetadata metadata) {
        if (!isVideoSource(source)) {
            return true;
        }
        Integer minDurationSeconds = source.getMinDurationSeconds();
        Long minViewCount = source.getMinViewCount();
        if ((minDurationSeconds == null || minDurationSeconds <= 0)
                && (minViewCount == null || minViewCount <= 0)) {
            return true;
        }
        if (minDurationSeconds != null && minDurationSeconds > 0
                && metadata.durationSeconds() != null
                && metadata.durationSeconds() < minDurationSeconds) {
            return false;
        }
        if (minDurationSeconds != null && minDurationSeconds > 0
                && metadata.durationSeconds() == null
                && metadata.viewCount() == null) {
            return false;
        }
        return minViewCount == null || minViewCount <= 0
                || (metadata.viewCount() != null && metadata.viewCount() >= minViewCount);
    }

    private static boolean isVideoSource(NewsroomContentProperties.Source source) {
        return "video".equals(normalizeContentType(source.getFeed()));
    }

    private static boolean isYouTubeShortsUrl(String url) {
        try {
            URI uri = URI.create(url);
            return domainMatches(firstNonBlank(uri.getHost(), ""), "youtube.com")
                    && uri.getPath() != null
                    && uri.getPath().startsWith("/shorts/");
        } catch (IllegalArgumentException exc) {
            return false;
        }
    }

    private static VideoMetadata parseYouTubeMetadata(String body, Long feedViewCount) {
        Long parsedViewCount = parseLong(YOUTUBE_VIEW_COUNT.matcher(body));
        return new VideoMetadata(
                parseLong(YOUTUBE_LENGTH_SECONDS.matcher(body)),
                parsedViewCount == null ? feedViewCount : parsedViewCount,
                parseYouTubeKeywords(body),
                true
        );
    }

    private static Long parseLong(Matcher matcher) {
        if (!matcher.find()) {
            return null;
        }
        try {
            return Long.parseLong(matcher.group(1));
        } catch (NumberFormatException exc) {
            return null;
        }
    }

    private static List<String> parseYouTubeKeywords(String body) {
        List<String> keywords = new ArrayList<>();
        Matcher keywordArray = YOUTUBE_KEYWORDS.matcher(body);
        if (keywordArray.find()) {
            try {
                JsonNode root = JSON.readTree(keywordArray.group(1));
                if (root.isArray()) {
                    root.forEach(node -> {
                        if (node.isTextual() && !blank(node.asText())) {
                            keywords.add(node.asText());
                        }
                    });
                }
            } catch (Exception ignored) {
                // Fall back to meta keywords below.
            }
        }

        Matcher metaKeywords = HTML_META_KEYWORDS.matcher(body);
        if (metaKeywords.find()) {
            for (String keyword : metaKeywords.group(1).split(",")) {
                String trimmed = firstNonBlank(keyword, null);
                if (trimmed != null) {
                    keywords.add(trimmed);
                }
            }
        }
        return keywords;
    }

    private static boolean withinMaxAge(
            NewsroomContentProperties.Source source,
            Instant publishedAt,
            Instant ingestedAt
    ) {
        Integer maxAgeDays = source.getMaxAgeDays();
        if (maxAgeDays == null || maxAgeDays <= 0) {
            return true;
        }
        if (publishedAt == null) {
            return false;
        }
        Instant threshold = ingestedAt.minus(Duration.ofDays(maxAgeDays));
        return !publishedAt.isBefore(threshold);
    }

    private static Long youtubeFeedViewCount(Element entry) {
        NodeList statisticsNodes = entry.getElementsByTagName("media:statistics");
        for (int index = 0; index < statisticsNodes.getLength(); index++) {
            Element statistics = asElement(statisticsNodes.item(index));
            if (statistics == null) {
                continue;
            }
            String views = statistics.getAttribute("views");
            if (!blank(views)) {
                try {
                    return Long.parseLong(views);
                } catch (NumberFormatException ignored) {
                    return null;
                }
            }
        }
        return null;
    }

    private static boolean reachedMaxItems(
            NewsroomContentProperties.Source source,
            List<RealEstateContentItemRequest> items
    ) {
        Integer maxItems = source.getMaxItems();
        return maxItems != null && maxItems > 0 && items.size() >= maxItems;
    }

    private RealEstateContentItemRequest contentRequest(
            NewsroomContentProperties.Source source,
            String title,
            String snippet,
            String url,
            String effectiveDomain,
            Instant publishedAt,
            Instant ingestedAt
    ) {
        return new RealEstateContentItemRequest(
                "newsroom-" + sha256(url).substring(0, 24),
                firstNonBlank(source.getSourceId(), source.getId()),
                normalizeContentType(source.getFeed()),
                title,
                snippet,
                url,
                firstNonBlank(effectiveDomain, domain(url)),
                publishedAt,
                "source: " + firstNonBlank(source.getId(), "rss"),
                firstNonBlank(source.getStatusLabel(), "수집 확인"),
                ingestedAt,
                firstNonBlank(source.getDataStatus(), "ok"),
                List.of()
        );
    }

    private static String normalizeContentType(String feed) {
        String normalized = firstNonBlank(feed, "news").toLowerCase(Locale.ROOT);
        return switch (normalized) {
            case "reports", "report" -> "report";
            case "videos", "video", "youtube" -> "video";
            case "links", "link", "blog", "community" -> "link";
            default -> "news";
        };
    }

    private static String childText(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() == 0) {
            return null;
        }
        return nodes.item(0).getTextContent();
    }

    private static String atomLink(Element entry) {
        NodeList links = entry.getElementsByTagName("link");
        for (int index = 0; index < links.getLength(); index++) {
            Element link = asElement(links.item(index));
            if (link == null) {
                continue;
            }
            String rel = link.getAttribute("rel");
            String href = link.getAttribute("href");
            if (!blank(href) && (blank(rel) || "alternate".equalsIgnoreCase(rel))) {
                return href;
            }
        }
        return null;
    }

    private static String rssSourceUrl(Element item) {
        NodeList sources = item.getElementsByTagName("source");
        for (int index = 0; index < sources.getLength(); index++) {
            Element source = asElement(sources.item(index));
            if (source == null) {
                continue;
            }
            String url = source.getAttribute("url");
            if (!blank(url)) {
                return url;
            }
        }
        return null;
    }

    private static Element asElement(Node node) {
        return node instanceof Element element ? element : null;
    }

    private static Instant parseDate(String value) {
        String trimmed = firstNonBlank(value, null);
        if (trimmed == null) {
            return null;
        }
        try {
            return OffsetDateTime.parse(trimmed, DateTimeFormatter.RFC_1123_DATE_TIME).toInstant();
        } catch (DateTimeParseException ignored) {
            try {
                return OffsetDateTime.parse(trimmed).toInstant();
            } catch (DateTimeParseException ignoredAgain) {
                try {
                    return Instant.parse(trimmed);
                } catch (DateTimeParseException ignoredThird) {
                    return null;
                }
            }
        }
    }

    private static String stripHtml(String value) {
        if (value == null) {
            return null;
        }
        return value.replaceAll("<[^>]+>", " ")
                .replace("&nbsp;", " ")
                .replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replaceAll("\\s+", " ")
                .trim();
    }

    private static String domain(String url) {
        if (blank(url)) {
            return null;
        }
        try {
            return URI.create(url).getHost();
        } catch (IllegalArgumentException exc) {
            return null;
        }
    }

    private static String trimTo(String value, int maxLength) {
        String trimmed = firstNonBlank(value, null);
        if (trimmed == null) {
            return null;
        }
        return trimmed.length() <= maxLength ? trimmed : trimmed.substring(0, maxLength);
    }

    private static String safe(String value) {
        return value == null ? "" : value;
    }

    private static boolean blank(String value) {
        return value == null || value.trim().isEmpty();
    }

    private static String firstNonBlank(String first, String second) {
        if (!blank(first)) {
            return first.trim();
        }
        return blank(second) ? null : second.trim();
    }

    private static String sha256(String value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(value.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException exc) {
            throw new IllegalStateException("SHA-256 algorithm is not available", exc);
        }
    }

    private record VideoMetadata(Long durationSeconds, Long viewCount, List<String> keywords, boolean available) {
        static VideoMetadata empty() {
            return new VideoMetadata(null, null, List.of(), true);
        }

        static VideoMetadata unavailable() {
            return new VideoMetadata(null, null, List.of(), false);
        }

        static VideoMetadata fromFeedViewCount(Long feedViewCount) {
            return new VideoMetadata(null, feedViewCount, List.of(), false);
        }

        String searchableText() {
            return String.join(" ", keywords);
        }
    }
}
