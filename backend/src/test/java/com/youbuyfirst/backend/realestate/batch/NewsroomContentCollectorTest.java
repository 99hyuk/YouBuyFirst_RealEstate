package com.youbuyfirst.backend.realestate.batch;

import com.youbuyfirst.backend.realestate.dto.RealEstateContentItemRequest;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class NewsroomContentCollectorTest {

    @Test
    void filtersVideoFeedByLongFormMetadataAndViewThreshold() {
        NewsroomContentProperties properties = new NewsroomContentProperties();
        NewsroomContentProperties.Source source = new NewsroomContentProperties.Source();
        source.setId("youtube-expert");
        source.setFeed("video");
        source.setSourceId("youtube:expert");
        source.setUrl("https://sources.test/youtube.atom");
        source.setDataStatus("ok");
        source.setRequiredTerms(List.of("apartment", "housing", "market"));
        source.setExcludedTerms(List.of("stock"));
        source.setMinDurationSeconds(600);
        source.setMinViewCount(10_000L);
        properties.setSources(List.of(source));

        RealEstateExternalFetchClient fetchClient = mock(RealEstateExternalFetchClient.class);
        when(fetchClient.fetch("https://sources.test/youtube.atom")).thenReturn(RealEstateExternalFetchResult.ok("""
                <?xml version="1.0" encoding="UTF-8"?>
                <feed xmlns="http://www.w3.org/2005/Atom">
                  <entry>
                    <title>Apartment shorts clip</title>
                    <link rel="alternate" href="https://www.youtube.com/shorts/short-demo"/>
                    <summary>Apartment market clip.</summary>
                    <published>2026-06-23T08:00:00Z</published>
                  </entry>
                  <entry>
                    <title>Apartment low view discussion</title>
                    <link rel="alternate" href="https://www.youtube.com/watch?v=low-view"/>
                    <summary>Apartment market discussion.</summary>
                    <published>2026-06-23T07:00:00Z</published>
                  </entry>
                  <entry>
                    <title>Housing short duration discussion</title>
                    <link rel="alternate" href="https://www.youtube.com/watch?v=short-duration"/>
                    <summary>Housing panel discussion.</summary>
                    <published>2026-06-23T06:00:00Z</published>
                  </entry>
                  <entry>
                    <title>Stock market analysis</title>
                    <link rel="alternate" href="https://www.youtube.com/watch?v=stock-market"/>
                    <summary>Stock market cycle discussion.</summary>
                    <published>2026-06-23T04:30:00Z</published>
                  </entry>
                  <entry>
                    <title>Expert panel full discussion</title>
                    <link rel="alternate" href="https://www.youtube.com/watch?v=full-discussion"/>
                    <summary>Housing market analysis with expert panel.</summary>
                    <published>2026-06-23T05:00:00Z</published>
                  </entry>
                </feed>
                """));
        when(fetchClient.fetch("https://www.youtube.com/watch?v=low-view"))
                .thenReturn(RealEstateExternalFetchResult.ok(youtubePlayerResponse(1_200, 9_999)));
        when(fetchClient.fetch("https://www.youtube.com/watch?v=short-duration"))
                .thenReturn(RealEstateExternalFetchResult.ok(youtubePlayerResponse(599, 50_000)));
        when(fetchClient.fetch("https://www.youtube.com/watch?v=full-discussion"))
                .thenReturn(RealEstateExternalFetchResult.ok(youtubePlayerResponse(1_800, 120_000)));

        List<RealEstateContentItemRequest> items = new NewsroomContentCollector(properties, fetchClient)
                .collect(Instant.parse("2026-06-23T00:00:00Z"));

        assertThat(items).extracting(RealEstateContentItemRequest::title)
                .containsExactly("Expert panel full discussion");
        assertThat(items.getFirst().domain()).isEqualTo("www.youtube.com");
    }

    @Test
    void acceptsVideoWhenYouTubeKeywordsCarryRealEstateTopic() {
        NewsroomContentProperties properties = new NewsroomContentProperties();
        NewsroomContentProperties.Source source = new NewsroomContentProperties.Source();
        source.setId("youtube-expert");
        source.setFeed("video");
        source.setSourceId("youtube:expert");
        source.setUrl("https://sources.test/youtube-keyword.atom");
        source.setDataStatus("ok");
        source.setRequiredTerms(List.of("부동산", "아파트", "전세"));
        source.setMinDurationSeconds(600);
        source.setMinViewCount(10_000L);
        properties.setSources(List.of(source));

        RealEstateExternalFetchClient fetchClient = mock(RealEstateExternalFetchClient.class);
        when(fetchClient.fetch("https://sources.test/youtube-keyword.atom")).thenReturn(RealEstateExternalFetchResult.ok("""
                <?xml version="1.0" encoding="UTF-8"?>
                <feed xmlns="http://www.w3.org/2005/Atom">
                  <entry>
                    <title>Expert roundtable full version</title>
                    <link rel="alternate" href="https://www.youtube.com/watch?v=tagged-realestate"/>
                    <summary>Macro cycle discussion with policy researchers.</summary>
                    <published>2026-06-23T08:00:00Z</published>
                  </entry>
                </feed>
                """));
        when(fetchClient.fetch("https://www.youtube.com/watch?v=tagged-realestate"))
                .thenReturn(RealEstateExternalFetchResult.ok(youtubePlayerResponse(
                        1_800,
                        120_000,
                        List.of("부동산", "아파트", "전세시장")
                )));

        List<RealEstateContentItemRequest> items = new NewsroomContentCollector(properties, fetchClient)
                .collect(Instant.parse("2026-06-23T00:00:00Z"));

        assertThat(items).extracting(RealEstateContentItemRequest::title)
                .containsExactly("Expert roundtable full version");
    }

    @Test
    void usesYoutubeAtomMediaDescriptionAndViewStatsWhenWatchMetadataUnavailable() {
        NewsroomContentProperties properties = new NewsroomContentProperties();
        NewsroomContentProperties.Source source = new NewsroomContentProperties.Source();
        source.setId("youtube-rss-media");
        source.setFeed("video");
        source.setSourceId("youtube:rss-media");
        source.setUrl("https://sources.test/youtube-media.atom");
        source.setDataStatus("ok");
        source.setRequiredTerms(List.of("재건축", "공급"));
        source.setMinDurationSeconds(600);
        source.setMinViewCount(10_000L);
        properties.setSources(List.of(source));

        RealEstateExternalFetchClient fetchClient = mock(RealEstateExternalFetchClient.class);
        when(fetchClient.fetch("https://sources.test/youtube-media.atom")).thenReturn(RealEstateExternalFetchResult.ok("""
                <?xml version="1.0" encoding="UTF-8"?>
                <feed xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
                  <entry>
                    <title>Urban planning walk full episode</title>
                    <link rel="alternate" href="https://www.youtube.com/watch?v=rss-media-video"/>
                    <published>2026-06-23T08:00:00Z</published>
                    <media:group>
                      <media:description>서울 재건축과 공급 정책을 현장에서 짚은 분석 영상입니다.</media:description>
                      <media:community>
                        <media:statistics views="34207"/>
                      </media:community>
                    </media:group>
                  </entry>
                  <entry>
                    <title>Low view redevelopment video</title>
                    <link rel="alternate" href="https://www.youtube.com/watch?v=low-rss-media-video"/>
                    <published>2026-06-23T07:00:00Z</published>
                    <media:group>
                      <media:description>재건축 공급 분석 영상입니다.</media:description>
                      <media:community>
                        <media:statistics views="9999"/>
                      </media:community>
                    </media:group>
                  </entry>
                </feed>
                """));
        when(fetchClient.fetch("https://www.youtube.com/watch?v=rss-media-video"))
                .thenReturn(RealEstateExternalFetchResult.failed(403, "blocked"));
        when(fetchClient.fetch("https://www.youtube.com/watch?v=low-rss-media-video"))
                .thenReturn(RealEstateExternalFetchResult.failed(403, "blocked"));

        List<RealEstateContentItemRequest> items = new NewsroomContentCollector(properties, fetchClient)
                .collect(Instant.parse("2026-06-23T00:00:00Z"));

        assertThat(items).extracting(RealEstateContentItemRequest::title)
                .containsExactly("Urban planning walk full episode");
    }

    @Test
    void filtersPersonalColumnRssByRecentAgeAndNoiseTerms() {
        NewsroomContentProperties properties = new NewsroomContentProperties();
        NewsroomContentProperties.Source source = new NewsroomContentProperties.Source();
        source.setId("naver-personal-column");
        source.setFeed("link");
        source.setSourceId("naver_blog:ppassong");
        source.setUrl("https://rss.blog.naver.com/ppassong.xml");
        source.setDataStatus("ok");
        source.setRequiredTerms(List.of("realestate column"));
        source.setAllowedDomains(List.of("blog.naver.com"));
        source.setExcludedTerms(List.of("stock", "class promo", "listing"));
        source.setMaxAgeDays(45);
        properties.setSources(List.of(source));

        RealEstateExternalFetchClient fetchClient = mock(RealEstateExternalFetchClient.class);
        when(fetchClient.fetch("https://rss.blog.naver.com/ppassong.xml")).thenReturn(RealEstateExternalFetchResult.ok("""
                <?xml version="1.0" encoding="UTF-8" ?>
                <rss version="2.0">
                  <channel>
                    <item>
                      <title>Realestate column on transit access</title>
                      <link>https://blog.naver.com/ppassong/224323087418?fromRss=true</link>
                      <description>realestate column on infrastructure and redevelopment flow.</description>
                      <pubDate>Mon, 22 Jun 2026 09:08:09 +0900</pubDate>
                    </item>
                    <item>
                      <title>Stock portfolio structure</title>
                      <link>https://blog.naver.com/ppassong/224324300024?fromRss=true</link>
                      <description>stock portfolio story.</description>
                      <pubDate>Tue, 23 Jun 2026 10:32:09 +0900</pubDate>
                    </item>
                    <item>
                      <title>Old realestate column</title>
                      <link>https://blog.naver.com/ppassong/223000000000?fromRss=true</link>
                      <description>realestate column from an old archive.</description>
                      <pubDate>Fri, 28 Nov 2025 11:18:44 +0900</pubDate>
                    </item>
                    <item>
                      <title>realestate listing promotion</title>
                      <link>https://blog.naver.com/ppassong/224000000000?fromRss=true</link>
                      <description>listing promotion.</description>
                      <pubDate>Tue, 23 Jun 2026 09:30:00 +0900</pubDate>
                    </item>
                  </channel>
                </rss>
                """));

        List<RealEstateContentItemRequest> items = new NewsroomContentCollector(properties, fetchClient)
                .collect(Instant.parse("2026-06-23T00:00:00Z"));

        assertThat(items).extracting(RealEstateContentItemRequest::title)
                .containsExactly("Realestate column on transit access");
    }

    @Test
    void filtersRssFeedByAllowedSourceDomainAndExcludedTerms() {
        NewsroomContentProperties properties = new NewsroomContentProperties();
        NewsroomContentProperties.Source source = new NewsroomContentProperties.Source();
        source.setId("expert-report-search");
        source.setFeed("report");
        source.setSourceId("expert_report_search");
        source.setUrl("https://sources.test/report.rss");
        source.setDataStatus("ok");
        source.setRequiredTerms(List.of("report", "review"));
        source.setRequiredTopicTerms(List.of("housing"));
        source.setAllowedDomains(List.of("kbthink.com", "www.hanaif.re.kr"));
        source.setExcludedTerms(List.of("listing"));
        properties.setSources(List.of(source));

        RealEstateExternalFetchClient fetchClient = mock(RealEstateExternalFetchClient.class);
        when(fetchClient.fetch("https://sources.test/report.rss")).thenReturn(RealEstateExternalFetchResult.ok("""
                <?xml version="1.0" encoding="UTF-8" ?>
                <rss version="2.0">
                  <channel>
                    <item>
                      <title>KB housing market review</title>
                      <link>https://news.google.com/rss/articles/report-demo</link>
                      <description>Monthly housing market report.</description>
                      <pubDate>Tue, 23 Jun 2026 09:30:00 GMT</pubDate>
                      <source url="https://kbthink.com">KB Think</source>
                    </item>
                    <item>
                      <title>Media article mentioning report</title>
                      <link>https://news.google.com/rss/articles/news-demo</link>
                      <description>News article, not expert source.</description>
                      <pubDate>Tue, 23 Jun 2026 09:20:00 GMT</pubDate>
                      <source url="https://media.example.com">Media</source>
                    </item>
                    <item>
                      <title>KB housing news article</title>
                      <link>https://news.google.com/rss/articles/housing-news-demo</link>
                      <description>Housing prices rose this week.</description>
                      <pubDate>Tue, 23 Jun 2026 09:15:00 GMT</pubDate>
                      <source url="https://kbthink.com">KB Think</source>
                    </item>
                    <item>
                      <title>Future industry report</title>
                      <link>https://news.google.com/rss/articles/industry-report-demo</link>
                      <description>Future industry research report.</description>
                      <pubDate>Tue, 23 Jun 2026 09:12:00 GMT</pubDate>
                      <source url="https://kbthink.com">KB Think</source>
                    </item>
                    <item>
                      <title>Apartment listing report</title>
                      <link>https://news.google.com/rss/articles/listing-demo</link>
                      <description>Listing promotion.</description>
                      <pubDate>Tue, 23 Jun 2026 09:10:00 GMT</pubDate>
                      <source url="https://kbthink.com">KB Think</source>
                    </item>
                  </channel>
                </rss>
                """));

        List<RealEstateContentItemRequest> items = new NewsroomContentCollector(properties, fetchClient)
                .collect(Instant.parse("2026-06-23T00:00:00Z"));

        assertThat(items).extracting(RealEstateContentItemRequest::title)
                .containsExactly("KB housing market review");
        assertThat(items.getFirst().domain()).isEqualTo("kbthink.com");
    }

    private static String youtubePlayerResponse(long lengthSeconds, long viewCount) {
        return youtubePlayerResponse(lengthSeconds, viewCount, List.of());
    }

    private static String youtubePlayerResponse(long lengthSeconds, long viewCount, List<String> keywords) {
        String keywordJson = keywords.stream()
                .map(keyword -> "\"" + keyword + "\"")
                .reduce((left, right) -> left + "," + right)
                .orElse("");
        return """
                <html><script>
                var ytInitialPlayerResponse = {"videoDetails":{"lengthSeconds":"%d","viewCount":"%d","keywords":[%s]}};
                </script></html>
                """.formatted(lengthSeconds, viewCount, keywordJson);
    }
}
