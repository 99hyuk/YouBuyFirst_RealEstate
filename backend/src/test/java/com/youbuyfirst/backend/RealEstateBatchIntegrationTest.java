package com.youbuyfirst.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.realestate.batch.RealEstateBatchUpdateEvent;
import com.youbuyfirst.backend.realestate.batch.RealEstateBatchUpdatePublisher;
import com.youbuyfirst.backend.realestate.batch.RealEstateExternalFetchClient;
import com.youbuyfirst.backend.realestate.batch.RealEstateExternalFetchResult;
import com.youbuyfirst.backend.realestate.RealEstateContentItem;
import com.youbuyfirst.backend.realestate.RealEstateContentItemRepository;
import com.youbuyfirst.backend.realestate.RealEstateMarketFact;
import com.youbuyfirst.backend.realestate.RealEstateMarketFactRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobParameters;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.core.env.Environment;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@SpringBootTest(
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = {
                "app.realestate.batch.scheduling-enabled=false",
                "app.realestate.newsroom.sources[0].id=test-news",
                "app.realestate.newsroom.sources[0].feed=news",
                "app.realestate.newsroom.sources[0].source-id=test_news_rss",
                "app.realestate.newsroom.sources[0].url=https://sources.test/news.rss",
                "app.realestate.newsroom.sources[0].status-label=수집 확인",
                "app.realestate.newsroom.sources[0].data-status=ok",
                "app.realestate.newsroom.sources[1].id=test-video",
                "app.realestate.newsroom.sources[1].feed=video",
                "app.realestate.newsroom.sources[1].source-id=youtube:trusted",
                "app.realestate.newsroom.sources[1].url=https://sources.test/video.atom",
                "app.realestate.newsroom.sources[1].status-label=collected",
                "app.realestate.newsroom.sources[1].data-status=ok",
                "app.realestate.newsroom.sources[1].required-terms[0]=apartment",
                "app.realestate.newsroom.sources[1].allowed-domains[0]=www.youtube.com",
                "app.realestate.newsroom.sources[1].max-items=1",
                "app.realestate.newsroom.sources[2].id=test-blog",
                "app.realestate.newsroom.sources[2].feed=link",
                "app.realestate.newsroom.sources[2].source-id=blog:trusted",
                "app.realestate.newsroom.sources[2].url=https://sources.test/blog.rss",
                "app.realestate.newsroom.sources[2].status-label=collected",
                "app.realestate.newsroom.sources[2].data-status=ok",
                "app.realestate.newsroom.sources[2].required-terms[0]=apartment",
                "app.realestate.newsroom.sources[2].allowed-domains[0]=blog.example.com",
                "app.realestate.newsroom.sources[2].max-items=1",
                "app.realestate.newsroom.sources[3].id=test-blog-extra",
                "app.realestate.newsroom.sources[3].feed=link",
                "app.realestate.newsroom.sources[3].source-id=blog:trusted",
                "app.realestate.newsroom.sources[3].url=https://sources.test/blog.rss",
                "app.realestate.newsroom.sources[3].status-label=collected",
                "app.realestate.newsroom.sources[3].data-status=ok",
                "app.realestate.newsroom.sources[3].required-terms[0]=apartment",
                "app.realestate.newsroom.sources[3].allowed-domains[0]=blog.example.com",
                "app.realestate.newsroom.sources[3].max-items=1",
                "app.realestate.batch.reb-weekly-price-index-url=https://sources.test/reb-weekly.csv"
        }
)
@ActiveProfiles("test")
class RealEstateBatchIntegrationTest {

    @Autowired
    private JobLauncher jobLauncher;

    @Autowired
    @Qualifier("newsroomContentRefreshJob")
    private Job newsroomContentRefreshJob;

    @Autowired
    @Qualifier("marketDataScheduleRefreshJob")
    private Job marketDataScheduleRefreshJob;

    @Autowired
    @Qualifier("rebWeeklyPriceIndexRefreshJob")
    private Job rebWeeklyPriceIndexRefreshJob;

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private Environment environment;

    @Autowired
    private RealEstateMarketFactRepository marketFactRepository;

    @Autowired
    private RealEstateContentItemRepository contentItemRepository;

    @MockBean
    private RealEstateExternalFetchClient externalFetchClient;

    @MockBean
    private RealEstateBatchUpdatePublisher batchUpdatePublisher;

    @BeforeEach
    void defaultUnstubbedFetchesFail() {
        when(externalFetchClient.fetch(anyString()))
                .thenReturn(RealEstateExternalFetchResult.failed(404, "not stubbed"));
        when(externalFetchClient.postForm(anyString(), anyMap(), anyMap()))
                .thenReturn(RealEstateExternalFetchResult.failed(404, "not stubbed"));
    }

    @Test
    void batchSchedulingDefaultsMatchNewsroomAndScheduleCadence() {
        assertThat(environment.getProperty("app.realestate.batch.newsroom-cron"))
                .isEqualTo("0 20 */2 * * *");
        assertThat(environment.getProperty("app.realestate.batch.schedule-cron"))
                .isEqualTo("0 10 4 * * *");
        assertThat(environment.getProperty("app.realestate.batch.reb-weekly-price-index-cron"))
                .isEqualTo("0 30 8 * * THU");
    }

    @Test
    void newsroomContentRefreshJobStoresGlobalContentWithoutTargetLinks() throws Exception {
        when(externalFetchClient.fetch("https://sources.test/news.rss")).thenReturn(
                RealEstateExternalFetchResult.ok("""
                        <?xml version="1.0" encoding="UTF-8" ?>
                        <rss version="2.0">
                          <channel>
                            <item>
                              <title>전국 부동산 정책 점검</title>
                              <link>https://www.hankyung.com/realestate/article/demo</link>
                              <description>공식 일정과 시장 데이터를 함께 확인해야 한다는 기사입니다.</description>
                              <pubDate>Mon, 22 Jun 2026 09:00:00 GMT</pubDate>
                              <source url="https://www.hankyung.com/">한국경제</source>
                            </item>
                          </channel>
                        </rss>
                        """)
        );

        jobLauncher.run(newsroomContentRefreshJob, uniqueParameters("newsroom"));

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/newsroom?feed=news&page=1&pageSize=10",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode items = objectMapper.readTree(response.getBody()).path("items");
        JsonNode item = firstItemWithTitle(items, "전국 부동산 정책 점검");
        assertThat(item).isNotNull();
        assertThat(item.path("contentType").asText()).isEqualTo("news");
        assertThat(item.path("sourceId").asText()).isEqualTo("test_news_rss");
        assertThat(item.path("domain").asText()).isEqualTo("www.hankyung.com");
        assertThat(item.path("targetId").isNull()).isTrue();
        assertThat(item.path("linkType").isNull()).isTrue();
        assertThat(item.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(item.path("statusLabel").asText()).isEqualTo("수집 확인");
        verify(batchUpdatePublisher).publish(argThat((RealEstateBatchUpdateEvent event) ->
                "newsroom".equals(event.topic())
                        && event.acceptedItems() == 1
                        && event.month() == null
                        && event.refreshedAt() != null
                ));
    }

    @Test
    void newsroomContentRefreshJobCollectsTrustedVideoFeedsWithSourceFilters() throws Exception {
        when(externalFetchClient.fetch("https://sources.test/video.atom")).thenReturn(
                RealEstateExternalFetchResult.ok("""
                        <?xml version="1.0" encoding="UTF-8"?>
                        <feed xmlns="http://www.w3.org/2005/Atom">
                          <entry>
                            <title>Latest apartment market video</title>
                            <link rel="alternate" href="https://www.youtube.com/watch?v=apartment-latest"/>
                            <summary>Apartment supply and jeonse market commentary.</summary>
                            <published>2026-06-23T08:00:00+09:00</published>
                          </entry>
                          <entry>
                            <title>General cooking video</title>
                            <link rel="alternate" href="https://www.youtube.com/watch?v=cooking"/>
                            <summary>Kitchen recipe only.</summary>
                            <published>2026-06-23T07:00:00+09:00</published>
                          </entry>
                        </feed>
                        """)
        );
        jobLauncher.run(newsroomContentRefreshJob, uniqueParameters("newsroom-trusted"));

        JsonNode videos = objectMapper.readTree(restTemplate.getForObject(
                "/api/realestate/newsroom?feed=videos&page=1&pageSize=10",
                String.class
        )).path("items");

        JsonNode video = firstItemWithTitle(videos, "Latest apartment market video");
        assertThat(video).isNotNull();
        assertThat(video.path("contentType").asText()).isEqualTo("video");
        assertThat(video.path("sourceId").asText()).isEqualTo("youtube:trusted");
        assertThat(video.path("domain").asText()).isEqualTo("www.youtube.com");
        assertThat(video.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(firstItemWithTitle(videos, "General cooking video")).isNull();
        verify(batchUpdatePublisher).publish(argThat((RealEstateBatchUpdateEvent event) ->
                "newsroom".equals(event.topic())
                        && event.acceptedItems() >= 1
                        && event.refreshedAt() != null
        ));
    }

    @Test
    void newsroomContentRefreshJobPreservesPreviouslyAcceptedVideoItems() throws Exception {
        Instant previousRun = Instant.parse("2026-06-22T00:00:00Z");
        RealEstateContentItem existingVideo = new RealEstateContentItem(
                "newsroom-existing-video-preserve",
                previousRun
        );
        existingVideo.update(
                "youtube:trusted",
                "video",
                "Existing apartment market analysis",
                "Apartment market context that should remain visible after refresh.",
                "https://www.youtube.com/watch?v=existing-preserved",
                "www.youtube.com",
                previousRun,
                "source: test-video",
                "collected",
                previousRun,
                "ok",
                previousRun
        );
        contentItemRepository.save(existingVideo);

        when(externalFetchClient.fetch("https://sources.test/video.atom")).thenReturn(
                RealEstateExternalFetchResult.ok("""
                        <?xml version="1.0" encoding="UTF-8"?>
                        <feed xmlns="http://www.w3.org/2005/Atom">
                          <entry>
                            <title>Fresh apartment market video</title>
                            <link rel="alternate" href="https://www.youtube.com/watch?v=fresh-video"/>
                            <summary>Apartment supply and jeonse market commentary.</summary>
                            <published>2026-06-23T08:00:00+09:00</published>
                          </entry>
                        </feed>
                        """)
        );

        jobLauncher.run(newsroomContentRefreshJob, uniqueParameters("newsroom-preserve-video"));

        JsonNode videos = objectMapper.readTree(restTemplate.getForObject(
                "/api/realestate/newsroom?feed=videos&page=1&pageSize=100",
                String.class
        )).path("items");

        JsonNode existing = firstItemWithTitle(videos, "Existing apartment market analysis");
        assertThat(existing).isNotNull();
        assertThat(existing.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(firstItemWithTitle(videos, "Fresh apartment market video")).isNotNull();
    }

    @Test
    void marketDataScheduleRefreshJobMaterializesMonthlyCalendarForFrontend() throws Exception {
        when(externalFetchClient.postForm(anyString(), anyMap(), anyMap())).thenAnswer(invocation -> {
            String url = invocation.getArgument(0, String.class);
            Map<String, String> form = invocation.getArgument(1);
            if ("https://www.reb.or.kr/r-one/portal/bbs/pres/searchBulletin.do".equals(url)
                    && "PRES01".equals(form.get("listSubCd"))) {
                return RealEstateExternalFetchResult.ok("""
                        {
                          "data": [
                            {
                              "bbsCd": "PRES",
                              "seq": 3931,
                              "noticeYn": "N",
                              "listSubCd": "PRES01",
                              "listSubNm": "주간아파트가격동향조사",
                              "bbsTit": "2026년 6월 15일 기준 주간아파트가격 동향",
                              "userDttm": "2026-06-18"
                            }
                          ]
                        }
                        """);
            }
            return RealEstateExternalFetchResult.ok("{\"data\":[]}");
        });
        when(externalFetchClient.fetch(anyString())).thenAnswer(invocation -> {
            String url = invocation.getArgument(0, String.class);
            if ("https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr>
                            <td class="bd_num">811</td>
                            <td class="bd_title"><a href="dtl.jsp?lcmspage=1&amp;id=95092134">전세 계약 전 ‘위험신호’ 알려준다, 안심전세앱 9월 개편</a></td>
                            <td class="bd_field">주택토지</td>
                            <td class="bd_date">2026-06-18</td>
                          </tr>
                        </tbody></table>
                        """);
            }
            if ("https://www.reb.or.kr/r-one/portal/compose/scheduleStatsPage.do".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr>
                            <td id="20260630">
                              <p class="ac calLink eventColorRENT" title="부동산거래(주택) 새창열림" data-relId="7000022">
                                <a href="javascript:goStatPage('7000022');" title="부동산거래(주택) 새창 열림">부동산거래(주택)</a>
                              </p>
                            </td>
                          </tr>
                        </tbody></table>
                        """);
            }
            if ("https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancListView.do".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr data-pbno="2026000289" data-hmno="2026000289" data-honm="신제주 동문디이스트 시그니처원Ⅱ">
                            <td>제주</td><td>민영</td><td>분양주택</td>
                            <td class="txt_l"><a href="#b" class="txt_l_b"><b>신제주 동문디이스트 시그니처원Ⅱ</b></a></td>
                            <td>동문건설 주식회사</td><td>1811-8838</td>
                            <td>2026-06-23</td><td>2026-06-24 ~ 2026-06-25</td><td>2026-06-30</td>
                          </tr>
                        </tbody></table>
                        """);
            }
            if ("https://khug.or.kr/houstar/web/p01/03/p010301.jsp?currentPage=1".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr>
                            <td class="txt_l">
                              <a href="/houstar/web/p01/03/p010301.jsp?articleId=37252&amp;currentPage=1&amp;mode=S">2026년 5월 민간아파트 분양가격 동향</a>
                            </td>
                            <td>2026.06.16</td>
                          </tr>
                        </tbody></table>
                        """);
            }
            if ("https://stat.molit.go.kr/portal/notice/scheduleList.do".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr>
                            <td>17</td>
                            <td class="mobile-show tl">
                              <a href="/portal/cate/viewChk.do?hRsId=32" target="_blank">미분양주택현황</a>
                              <div><dl><dt>다음공표일</dt><dd>2026-06-28</dd></dl></div>
                            </td>
                            <td>승인통계</td><td>주택정책과</td><td>044-201-0000</td><td>매월</td><td>익월말</td><td>2026-06-28</td>
                          </tr>
                        </tbody></table>
                        """);
            }
            if ("https://www.bok.or.kr/portal/singl/crncyPolicyDrcMtg/listYear.do?menuNo=200755&mtgSe=A".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr><th scope="row">06월 25일(목)</th><td></td><td class="tal"></td></tr>
                          <tr><th scope="row">07월 16일(목)</th><td></td><td class="tal"></td></tr>
                        </tbody></table>
                        """);
            }
            if ("https://www.bok.or.kr/portal/stats/statsPublictSchdul/listCldr.do?date=2026-06&menuNo=200775".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr><th>공표일</th><th>시각</th><th>대상통계</th><th>비고</th></tr>
                          <tr><td>2026-06-25</td><td>12:00</td><td>2026년 5월 금융기관 가중평균금리</td><td></td></tr>
                          <tr><td>2026-06-26</td><td>6:00</td><td>2026년 6월 소비자동향조사 결과</td><td></td></tr>
                          <tr><td>2026-06-27</td><td>8:00</td><td>2026년 5월 국제수지(잠정)</td><td></td></tr>
                        </tbody></table>
                        """);
            }
            return RealEstateExternalFetchResult.ok("<html>ok</html>");
        });

        JobParameters parameters = new JobParametersBuilder(uniqueParameters("schedule"))
                .addString("month", "2026-06")
                .toJobParameters();
        jobLauncher.run(marketDataScheduleRefreshJob, parameters);

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/market-data-schedules?month=2026-06",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode root = objectMapper.readTree(response.getBody());
        assertThat(root.path("month").asText()).isEqualTo("2026-06");

        JsonNode events = root.path("scheduleEvents");
        assertThat(firstItemWithId(events, "reb-r-one-weekly-2026-06-03")).isNull();
        assertThat(firstItemWithId(events, "rt-molit-2026-06-05")).isNull();
        assertThat(firstItemWithId(events, "applyhome-2026-06-16")).isNull();
        assertThat(firstItemWithId(events, "molit-policy-2026-06-20")).isNull();
        assertThat(firstItemWithId(events, "hug-market-2026-06-25")).isNull();
        assertThat(firstItemWithId(events, "month-close-2026-06-30")).isNull();

        JsonNode rebPublished = firstItemWithId(events, "reb-r-one-published-pres01-3931");
        assertThat(rebPublished).isNotNull();
        assertThat(rebPublished.path("date").asText()).isEqualTo("2026-06-18");
        assertThat(rebPublished.path("title").asText()).isEqualTo("2026년 6월 15일 기준 주간아파트가격 동향");
        assertThat(rebPublished.path("summary").asText())
                .isEqualTo("한국부동산원 주간아파트가격동향조사 공표자료: 2026년 6월 15일 기준 주간아파트가격 동향");
        assertThat(rebPublished.path("link").asText())
                .isEqualTo("https://www.reb.or.kr/r-one/portal/bbs/pres/selectBulletinPage.do?bbsCd=PRES&seq=3931&noticeYn=N");
        assertThat(rebPublished.path("status").asText()).isEqualTo("공표 확인");
        assertThat(rebPublished.path("dataStatus").asText()).isEqualTo("published");

        JsonNode rebSchedule = firstItemWithId(events, "reb-r-one-schedule-7000022-2026-06-30");
        assertThat(rebSchedule).isNotNull();
        assertThat(rebSchedule.path("date").asText()).isEqualTo("2026-06-30");
        assertThat(rebSchedule.path("title").asText()).isEqualTo("부동산거래(주택) 공표 예정");
        assertThat(rebSchedule.path("summary").asText())
                .isEqualTo("R-ONE 통계공표일정 2026-06-30 기준 부동산거래(주택) 공식 공표 일정입니다.");
        assertThat(rebSchedule.path("link").asText())
                .isEqualTo("https://www.reb.or.kr/r-one/portal/stat/easyStatPage.do?cateId=7000022");
        assertThat(rebSchedule.path("status").asText()).isEqualTo("공식 일정");
        assertThat(rebSchedule.path("dataStatus").asText()).isEqualTo("scheduled");

        JsonNode molitStatSchedule = firstItemWithId(events, "molit-stat-schedule-32-2026-06-28");
        assertThat(molitStatSchedule).isNotNull();
        assertThat(molitStatSchedule.path("title").asText()).isEqualTo("미분양주택현황 공표 예정");
        assertThat(molitStatSchedule.path("summary").asText())
                .isEqualTo("통계누리 다음공표일 2026-06-28 기준 미분양주택현황 공식 통계 일정입니다.");
        assertThat(molitStatSchedule.path("link").asText())
                .isEqualTo("https://stat.molit.go.kr/portal/cate/viewChk.do?hRsId=32");
        assertThat(molitStatSchedule.path("status").asText()).isEqualTo("공식 일정");
        assertThat(molitStatSchedule.path("dataStatus").asText()).isEqualTo("scheduled");

        JsonNode bokSchedule = firstItemWithId(events, "bok-rate-meeting-2026-06-25");
        assertThat(bokSchedule).isNotNull();
        assertThat(bokSchedule.path("title").asText()).isEqualTo("한국은행 통화정책방향 결정회의");
        assertThat(bokSchedule.path("link").asText())
                .isEqualTo("https://www.bok.or.kr/portal/singl/crncyPolicyDrcMtg/listYear.do?menuNo=200755&mtgSe=A");
        assertThat(bokSchedule.path("status").asText()).isEqualTo("공식 일정");
        assertThat(bokSchedule.path("dataStatus").asText()).isEqualTo("scheduled");

        JsonNode bokWeightedRate = firstItemWithTitle(events, "2026년 5월 금융기관 가중평균금리 공표 예정");
        assertThat(bokWeightedRate).isNotNull();
        assertThat(bokWeightedRate.path("date").asText()).isEqualTo("2026-06-25");
        assertThat(bokWeightedRate.path("category").asText()).isEqualTo("금융");
        assertThat(bokWeightedRate.path("source").asText()).isEqualTo("한국은행 경제통계");
        assertThat(bokWeightedRate.path("summary").asText())
                .isEqualTo("한국은행 월간통계 공표일정 기준 2026-06-25 12:00 공개 예정인 금융·거시 통계입니다.");
        assertThat(bokWeightedRate.path("link").asText())
                .isEqualTo("https://www.bok.or.kr/portal/stats/statsPublictSchdul/listCldr.do?date=2026-06&menuNo=200775");
        assertThat(bokWeightedRate.path("status").asText()).isEqualTo("공식 일정");
        assertThat(bokWeightedRate.path("dataStatus").asText()).isEqualTo("scheduled");
        assertThat(firstItemWithTitle(events, "2026년 5월 국제수지(잠정) 공표 예정")).isNull();

        JsonNode applyHomePublished = firstItemWithId(events, "applyhome-published-2026000289");
        assertThat(applyHomePublished).isNotNull();
        assertThat(applyHomePublished.path("date").asText()).isEqualTo("2026-06-23");
        assertThat(applyHomePublished.path("title").asText()).isEqualTo("신제주 동문디이스트 시그니처원Ⅱ 입주자모집공고");
        assertThat(applyHomePublished.path("summary").asText())
                .isEqualTo("모집공고일 2026-06-23, 청약기간 2026-06-24~2026-06-25, 당첨자 발표 2026-06-30인 청약Home 공고입니다.");
        assertThat(applyHomePublished.path("link").asText())
                .isEqualTo("https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancDetail.do?houseManageNo=2026000289&pblancNo=2026000289");
        assertThat(applyHomePublished.path("status").asText()).isEqualTo("공표 확인");
        assertThat(applyHomePublished.path("dataStatus").asText()).isEqualTo("published");

        JsonNode applyHomeStart = firstItemWithId(events, "applyhome-application-start-2026000289-2026-06-24");
        assertThat(applyHomeStart).isNotNull();
        assertThat(applyHomeStart.path("title").asText()).isEqualTo("신제주 동문디이스트 시그니처원Ⅱ 청약 접수 시작");
        assertThat(applyHomeStart.path("link").asText()).isEqualTo(applyHomePublished.path("link").asText());
        assertThat(applyHomeStart.path("dataStatus").asText()).isEqualTo("scheduled");

        JsonNode applyHomeEnd = firstItemWithId(events, "applyhome-application-end-2026000289-2026-06-25");
        assertThat(applyHomeEnd).isNotNull();
        assertThat(applyHomeEnd.path("title").asText()).isEqualTo("신제주 동문디이스트 시그니처원Ⅱ 청약 접수 마감");
        assertThat(applyHomeEnd.path("link").asText()).isEqualTo(applyHomePublished.path("link").asText());
        assertThat(applyHomeEnd.path("dataStatus").asText()).isEqualTo("scheduled");

        JsonNode applyHomeWinner = firstItemWithId(events, "applyhome-winner-2026000289-2026-06-30");
        assertThat(applyHomeWinner).isNotNull();
        assertThat(applyHomeWinner.path("title").asText()).isEqualTo("신제주 동문디이스트 시그니처원Ⅱ 당첨자 발표");
        assertThat(applyHomeWinner.path("link").asText()).isEqualTo(applyHomePublished.path("link").asText());
        assertThat(applyHomeWinner.path("dataStatus").asText()).isEqualTo("scheduled");

        JsonNode hugPublished = firstItemWithId(events, "hug-market-published-37252");
        assertThat(hugPublished).isNotNull();
        assertThat(hugPublished.path("date").asText()).isEqualTo("2026-06-16");
        assertThat(hugPublished.path("title").asText()).isEqualTo("2026년 5월 민간아파트 분양가격 동향");
        assertThat(hugPublished.path("summary").asText())
                .isEqualTo("HUG 주택도시보증공사 분양시장 공표자료: 2026년 5월 민간아파트 분양가격 동향");
        assertThat(hugPublished.path("link").asText())
                .isEqualTo("https://khug.or.kr/houstar/web/p01/03/p010301.jsp?articleId=37252&currentPage=1&mode=S");
        assertThat(hugPublished.path("status").asText()).isEqualTo("공표 확인");
        assertThat(hugPublished.path("dataStatus").asText()).isEqualTo("published");

        JsonNode molitPublished = firstItemWithId(events, "molit-policy-published-95092134");
        assertThat(molitPublished).isNotNull();
        assertThat(molitPublished.path("date").asText()).isEqualTo("2026-06-18");
        assertThat(molitPublished.path("title").asText())
                .isEqualTo("전세 계약 전 ‘위험신호’ 알려준다, 안심전세앱 9월 개편");
        assertThat(molitPublished.path("summary").asText())
                .isEqualTo("국토교통부 주택토지 보도자료: 전세 계약 전 ‘위험신호’ 알려준다, 안심전세앱 9월 개편");
        assertThat(molitPublished.path("link").asText())
                .isEqualTo("https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?lcmspage=1&id=95092134");
        assertThat(molitPublished.path("status").asText()).isEqualTo("공표 확인");
        assertThat(molitPublished.path("dataStatus").asText()).isEqualTo("published");

        JsonNode sources = root.path("sourceLinks");
        JsonNode applyHome = firstItemWithId(sources, "applyhome");
        assertThat(applyHome).isNotNull();
        assertThat(applyHome.path("title").asText()).isEqualTo("청약Home");
        assertThat(applyHome.path("label").asText()).isEqualTo("청약·분양");
        assertThat(applyHome.path("status").asText()).isEqualTo("확인 완료");
        assertThat(applyHome.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(applyHome.path("stale").asBoolean()).isFalse();
        assertThat(applyHome.path("lastCheckedAt").asText()).isNotBlank();
        JsonNode bokStat = firstItemWithId(sources, "bok-stat");
        assertThat(bokStat).isNotNull();
        assertThat(bokStat.path("title").asText()).isEqualTo("한국은행 경제통계");
        assertThat(bokStat.path("dataStatus").asText()).isEqualTo("ok");
        assertEveryScheduleHasContextLink(events);
        verify(batchUpdatePublisher).publish(argThat((RealEstateBatchUpdateEvent event) ->
                "market-data-schedules".equals(event.topic())
                        && "2026-06".equals(event.month())
                        && event.acceptedItems() > 0
                        && event.refreshedAt() != null
        ));
    }

    @Test
    void marketDataScheduleRefreshJobCollectsPublicSupplyFinanceAndOfficialPriceRows() throws Exception {
        when(externalFetchClient.postForm(anyString(), anyMap(), anyMap()))
                .thenReturn(RealEstateExternalFetchResult.ok("{\"data\":[]}"));
        when(externalFetchClient.fetch(anyString())).thenAnswer(invocation -> {
            String url = invocation.getArgument(0, String.class);
            if ("https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1027".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr>
                            <td>
                              <button type="button" class="wrtancInfoBtn" data-id1="2026040001" data-id2="01" data-id3="05" data-id4="05">상세</button>
                              <a href="#none">고양창릉 A-4BL 공공분양주택 입주자모집공고</a>
                            </td>
                            <td>공공분양</td><td>경기</td><td>2026.04.15</td><td>2026.04.30</td><td>공고중</td>
                          </tr>
                          <tr>
                            <td>
                              <button type="button" class="wrtancInfoBtn" data-id1="2015122300020064" data-id2="01" data-id3="05" data-id4="05">상세</button>
                              <a href="#none">분양주택</a>
                            </td>
                            <td>분양주택</td><td>경남</td><td>2026.04.09</td><td>2026.04.30</td><td>공고중</td>
                          </tr>
                          <tr>
                            <td>
                              <button type="button" class="wrtancInfoBtn" data-id1="2015122300020098" data-id2="01" data-id3="05" data-id4="05">상세</button>
                              <a href="#none">창원시 매입임대 잔여주택 일반매각 선착순 동호지정 공고</a>
                            </td>
                            <td>매입임대</td><td>경남</td><td>2026.04.10</td><td>2026.04.30</td><td>공고중</td>
                          </tr>
                          <tr>
                            <td>
                              <button type="button" class="wrtancInfoBtn" data-id1="2015122300020155" data-id2="01" data-id3="05" data-id4="05">상세</button>
                              <a href="#none">[정정공고]광주첨단 H-1,2BL 행복주택 예비입주자 모집</a>
                            </td>
                            <td>행복주택</td><td>광주</td><td>2026.04.15</td><td>2026.04.30</td><td>공고중</td>
                          </tr>
                        </tbody></table>
                        """);
            }
            if ("https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1026".equals(url)) {
                return RealEstateExternalFetchResult.ok("<table><tbody></tbody></table>");
            }
            if ("https://housing.seoul.go.kr/site/main/sh/publicLease/07/list".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <ul>
                          <li>
                            <a href="/site/main/sh/publicLease/07/view?seq=sh202604">서울 장기전세주택 입주자모집공고</a>
                            <span>2026.04.16</span>
                          </li>
                        </ul>
                        """);
            }
            if ("https://www.gh.or.kr/gh/announcement-of-salerental001.do".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr>
                            <td>주택</td>
                            <td><a href="/gh/announcement-of-salerental001.do?articleNo=2231">광명학온 공공주택 분양 공고</a></td>
                            <td>주택사업부</td><td>26.04.17</td>
                          </tr>
                        </tbody></table>
                        """);
            }
            if ("https://www.ih.co.kr/main/sale_lease/notice.jsp".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <ul>
                          <li>
                            <a href="/main/sale_lease/notice_view.jsp?seq=77">검단 행복주택 예비입주자 모집공고</a>
                            <span>2026.04.18</span>
                          </li>
                        </ul>
                        """);
            }
            if ("https://www.ih.co.kr/main/sale_lease/board/house_notice.jsp".equals(url)) {
                return RealEstateExternalFetchResult.ok("<ul></ul>");
            }
            if ("https://www.fsc.go.kr/no010101".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <ul>
                          <li>
                            <a href="/no010101/86606?curPage=1">부동산 시장과 금융의 절연을 위한 - 26년도 가계부채 관리방안 발표</a>
                            <div class="day">2026-04-01</div>
                          </li>
                        </ul>
                        """);
            }
            if ("https://www.realtyprice.kr/notice/board/boardListAll.board".equals(url)) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr>
                            <td>11</td><td><span class="cate cate01">공동</span></td>
                            <td><a href="javascript:goDetail( 36 )">2026년 1월 1일 기준 공동주택가격 결정·공시 및 이의신청</a></td>
                            <td>2026-04-30</td>
                          </tr>
                        </tbody></table>
                        """);
            }
            return RealEstateExternalFetchResult.ok("<html>ok</html>");
        });

        jobLauncher.run(marketDataScheduleRefreshJob, new JobParametersBuilder(uniqueParameters("schedule-p2"))
                .addString("month", "2026-04")
                .toJobParameters());

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/market-data-schedules?month=2026-04",
                String.class
        );
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode root = objectMapper.readTree(response.getBody());
        JsonNode events = root.path("scheduleEvents");

        JsonNode lhSupply = firstItemWithId(events, "lh-apply-published-2026040001-2026-04-15");
        assertThat(lhSupply).isNotNull();
        assertThat(lhSupply.path("title").asText()).isEqualTo("고양창릉 A-4BL 공공분양주택 입주자모집공고");
        assertThat(lhSupply.path("link").asText())
                .isEqualTo("https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do?panId=2026040001&ccrCnntSysDsCd=01&uppAisTpCd=05&aisTpCd=05");
        assertThat(lhSupply.path("dataStatus").asText()).isEqualTo("published");
        assertThat(firstItemWithId(events, "lh-apply-published-2015122300020064-2026-04-09")).isNull();
        assertThat(firstItemWithId(events, "lh-apply-published-2015122300020098-2026-04-10")).isNull();
        assertThat(firstItemWithId(events, "lh-apply-published-2015122300020155-2026-04-15")).isNull();

        JsonNode shSupply = firstItemWithId(events, "sh-housing-published-sh202604-2026-04-16");
        assertThat(shSupply).isNotNull();
        assertThat(shSupply.path("link").asText())
                .isEqualTo("https://housing.seoul.go.kr/site/main/sh/publicLease/07/view?seq=sh202604");

        JsonNode ghSupply = firstItemWithId(events, "gh-supply-published-2231-2026-04-17");
        assertThat(ghSupply).isNotNull();
        assertThat(ghSupply.path("link").asText())
                .isEqualTo("https://www.gh.or.kr/gh/announcement-of-salerental001.do?articleNo=2231");

        JsonNode ihSupply = firstItemWithId(events, "ih-supply-published-77-2026-04-18");
        assertThat(ihSupply).isNotNull();
        assertThat(ihSupply.path("link").asText())
                .isEqualTo("https://www.ih.co.kr/main/sale_lease/notice_view.jsp?seq=77");

        JsonNode fscPolicy = firstItemWithId(events, "fsc-policy-published-86606");
        assertThat(fscPolicy).isNotNull();
        assertThat(fscPolicy.path("category").asText()).isEqualTo("금융");
        assertThat(fscPolicy.path("link").asText()).isEqualTo("https://www.fsc.go.kr/no010101/86606?curPage=1");

        JsonNode realtyPrice = firstItemWithId(events, "realty-price-published-36");
        assertThat(realtyPrice).isNotNull();
        assertThat(realtyPrice.path("category").asText()).isEqualTo("공시가격");
        assertThat(realtyPrice.path("link").asText())
                .isEqualTo("https://www.realtyprice.kr/notice/board/boardDetailAll.board?seq=36");

        JsonNode sources = root.path("sourceLinks");
        assertThat(firstItemWithId(sources, "lh-apply")).isNotNull();
        assertThat(firstItemWithId(sources, "sh-housing")).isNotNull();
        assertThat(firstItemWithId(sources, "gh-supply")).isNotNull();
        assertThat(firstItemWithId(sources, "ih-supply")).isNotNull();
        assertThat(firstItemWithId(sources, "fsc-policy")).isNotNull();
        assertThat(firstItemWithId(sources, "realty-price")).isNotNull();
        assertEveryScheduleHasContextLink(events);
    }

    @Test
    void manualBatchRunEndpointLaunchesMarketDataScheduleJob() throws Exception {
        when(externalFetchClient.fetch(anyString())).thenReturn(RealEstateExternalFetchResult.ok("<html>ok</html>"));

        ResponseEntity<String> runResponse = restTemplate.postForEntity(
                "/internal/realestate/batch-jobs/marketDataScheduleRefreshJob/run?month=2026-08",
                null,
                String.class
        );

        assertThat(runResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode run = objectMapper.readTree(runResponse.getBody());
        assertThat(run.path("jobName").asText()).isEqualTo("marketDataScheduleRefreshJob");
        assertThat(run.path("status").asText()).isEqualTo("COMPLETED");
        assertThat(run.path("month").asText()).isEqualTo("2026-08");

        ResponseEntity<String> scheduleResponse = restTemplate.getForEntity(
                "/api/realestate/market-data-schedules?month=2026-08",
                String.class
        );
        assertThat(scheduleResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode events = objectMapper.readTree(scheduleResponse.getBody()).path("scheduleEvents");
        assertThat(events).isEmpty();
    }

    @Test
    void marketDataScheduleRefreshJobMarksFailedSourcesSeparatelyFromEmptyMonths() throws Exception {
        when(externalFetchClient.fetch(anyString())).thenAnswer(invocation -> {
            String url = invocation.getArgument(0, String.class);
            if ("https://stat.molit.go.kr/".equals(url)
                    || "https://stat.molit.go.kr/portal/notice/scheduleList.do".equals(url)) {
                return RealEstateExternalFetchResult.failed(503, "provider unavailable");
            }
            return RealEstateExternalFetchResult.ok("<html>ok</html>");
        });

        jobLauncher.run(marketDataScheduleRefreshJob, new JobParametersBuilder(uniqueParameters("schedule-source-error"))
                .addString("month", "2026-10")
                .toJobParameters());

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/market-data-schedules?month=2026-10",
                String.class
        );
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode root = objectMapper.readTree(response.getBody());
        assertThat(root.path("scheduleEvents")).isEmpty();

        JsonNode sources = root.path("sourceLinks");
        JsonNode molitStat = firstItemWithId(sources, "molit-stat");
        assertThat(molitStat).isNotNull();
        assertThat(molitStat.path("status").asText()).isEqualTo("확인 필요");
        assertThat(molitStat.path("dataStatus").asText()).isEqualTo("error");
        assertThat(molitStat.path("stale").asBoolean()).isTrue();

        JsonNode applyHome = firstItemWithId(sources, "applyhome");
        assertThat(applyHome).isNotNull();
        assertThat(applyHome.path("status").asText()).isEqualTo("확인 완료");
        assertThat(applyHome.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(applyHome.path("stale").asBoolean()).isFalse();
    }

    @Test
    void marketDataScheduleRefreshJobReplacesMonthWithLatestOfficialRows() throws Exception {
        AtomicBoolean includeApplyHomeNotice = new AtomicBoolean(true);
        when(externalFetchClient.fetch(anyString())).thenAnswer(invocation -> {
            String url = invocation.getArgument(0, String.class);
            if ("https://www.applyhome.co.kr/ai/aia/selectAPTLttotPblancListView.do".equals(url)
                    && includeApplyHomeNotice.get()) {
                return RealEstateExternalFetchResult.ok("""
                        <table><tbody>
                          <tr data-pbno="2026000901" data-hmno="2026000901" data-honm="검증 아파트">
                            <td>서울</td><td>민영</td><td>분양주택</td>
                            <td class="txt_l"><a href="#b" class="txt_l_b"><b>검증 아파트</b></a></td>
                            <td>검증 시행사</td><td>02-0000-0000</td>
                            <td>2026-09-10</td><td>2026-09-20 ~ 2026-09-21</td><td>2026-09-28</td>
                          </tr>
                        </tbody></table>
                        """);
            }
            return RealEstateExternalFetchResult.ok("<html>ok</html>");
        });

        jobLauncher.run(marketDataScheduleRefreshJob, new JobParametersBuilder(uniqueParameters("schedule-prune-first"))
                .addString("month", "2026-09")
                .toJobParameters());

        ResponseEntity<String> firstResponse = restTemplate.getForEntity(
                "/api/realestate/market-data-schedules?month=2026-09",
                String.class
        );
        JsonNode firstEvents = objectMapper.readTree(firstResponse.getBody()).path("scheduleEvents");
        assertThat(firstItemWithId(firstEvents, "applyhome-published-2026000901")).isNotNull();

        includeApplyHomeNotice.set(false);
        jobLauncher.run(marketDataScheduleRefreshJob, new JobParametersBuilder(uniqueParameters("schedule-prune-second"))
                .addString("month", "2026-09")
                .toJobParameters());

        ResponseEntity<String> secondResponse = restTemplate.getForEntity(
                "/api/realestate/market-data-schedules?month=2026-09",
                String.class
        );
        JsonNode secondEvents = objectMapper.readTree(secondResponse.getBody()).path("scheduleEvents");
        assertThat(firstItemWithId(secondEvents, "applyhome-published-2026000901")).isNull();
        assertThat(secondEvents).isEmpty();
    }

    @Test
    void rebWeeklyPriceIndexRefreshJobStoresWeeklyFactsAndRefreshesMapLayers() throws Exception {
        when(externalFetchClient.fetch("https://sources.test/reb-weekly.csv")).thenReturn(
                RealEstateExternalFetchResult.ok("""
                        targetId,legalDongCode,observedAt,indexValue,regionName
                        region-seoul-jongno,11110,2026-06-20,100.0,Seoul Jongno
                        region-seoul-jongno,11110,2026-06-27,101.0,Seoul Jongno
                        """)
        );

        JobParameters parameters = new JobParametersBuilder(uniqueParameters("reb-weekly"))
                .addString("asOf", "2026-06-27T00:00:00Z")
                .toJobParameters();
        jobLauncher.run(rebWeeklyPriceIndexRefreshJob, parameters);

        ResponseEntity<String> response = restTemplate.getForEntity(
                "/api/realestate/map/layers?layerType=sigungu&parentTargetId=region-seoul",
                String.class
        );

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        JsonNode root = objectMapper.readTree(response.getBody());
        JsonNode jongno = firstTargetWithId(root.path("targets"), "region-seoul-jongno");
        assertThat(jongno).isNotNull();
        JsonNode week = jongno.path("periods").path("week");
        assertThat(week.path("provider").asText()).isEqualTo("reb");
        assertThat(week.path("sourceLabel").asText()).isEqualTo("REB R-ONE weekly apartment sale price index");
        assertThat(week.path("dataStatus").asText()).isEqualTo("ok");
        assertThat(week.path("stale").asBoolean()).isFalse();
        assertThat(week.path("changePct").asDouble()).isEqualTo(1.0);
        assertThat(week.path("sampleCount").asInt()).isEqualTo(2);
        assertThat(jongno.path("periods").has("month")).isFalse();
        verify(batchUpdatePublisher).publish(argThat((RealEstateBatchUpdateEvent event) ->
                "map-layers".equals(event.topic())
                        && event.acceptedItems() >= 3
                        && event.month() == null
                        && event.refreshedAt() != null
        ));
    }

    @Test
    void rebWeeklyPriceIndexRefreshJobStoresSourceProvidedWeeklyIndexJson() throws Exception {
        when(externalFetchClient.fetch("https://sources.test/reb-weekly.csv")).thenReturn(
                RealEstateExternalFetchResult.ok("""
                        {
                          "DATA": [
                            {
                              "CATE1": "서울",
                              "CATE2": "서울",
                              "CATE3": "종로구",
                              "COL_20262510001OD": "100.80",
                              "COL_20262610001OD": "101.04",
                              "COL_20262610001PR": "0.24"
                            }
                          ]
                        }
                        """)
        );

        JobParameters parameters = new JobParametersBuilder(uniqueParameters("reb-weekly-json"))
                .addString("asOf", "2026-06-26T00:00:00Z")
                .toJobParameters();
        jobLauncher.run(rebWeeklyPriceIndexRefreshJob, parameters);

        RealEstateMarketFact fact = marketFactRepository
                .findByProviderAndProviderDatasetAndProviderObjectId(
                        "reb",
                        "reb_rone_weekly_apt_sale_price_index_region",
                        "reb_rone_weekly_apt_sale_price_index_region:T244183132827305:202626:11110"
                )
                .orElseThrow();
        JsonNode value = objectMapper.readTree(fact.getValueJson());

        assertThat(fact.getObservedAt().toString()).isEqualTo("2026-06-25");
        assertThat(fact.getFactType()).isEqualTo("price_index");
        assertThat(value.path("value").asDouble()).isEqualTo(101.04);
        assertThat(value.path("indexValue").asDouble()).isEqualTo(101.04);
        assertThat(value.path("unit").asText()).isEqualTo("지수");
        assertThat(value.path("metricCode").asText()).isEqualTo("reb_weekly_apt_sale_price_index_region");
        assertThat(value.path("sourceIndexProvided").asBoolean()).isTrue();
        assertThat(value.has("sourceChangeProvided")).isFalse();
        assertThat(value.has("previousIndexValue")).isFalse();
    }

    private static JobParameters uniqueParameters(String prefix) {
        return new JobParametersBuilder()
                .addString("testRunId", prefix + "-" + Instant.now().toEpochMilli())
                .toJobParameters();
    }

    private static JsonNode firstItemWithTitle(JsonNode items, String title) {
        for (JsonNode item : items) {
            if (title.equals(item.path("title").asText())) {
                return item;
            }
        }
        return null;
    }

    private static JsonNode firstItemWithId(JsonNode items, String id) {
        for (JsonNode item : items) {
            if (id.equals(item.path("id").asText())) {
                return item;
            }
        }
        return null;
    }

    private static void assertEveryScheduleHasContextLink(JsonNode items) {
        for (JsonNode item : items) {
            String id = item.path("id").asText();
            String link = item.path("link").asText();
            assertThat(link).describedAs(id + " link").isNotBlank();
            assertThat(link).describedAs(id + " context link").matches(".*("
                    + "selectBulletinPage\\.do"
                    + "|easyStatPage\\.do\\?cateId="
                    + "|viewChk\\.do"
                    + "|selectAPTLttotPblancDetail\\.do"
                    + "|selectWrtancInfo\\.do"
                    + "|articleId="
                    + "|/site/main/sh/publicLease/07/view"
                    + "|announcement-of-salerental001\\.do\\?articleNo="
                    + "|/main/sale_lease/notice_view\\.jsp"
                    + "|/no010101/"
                    + "|boardDetailAll\\.board\\?seq="
                    + "|/USR/NEWS/.*/dtl\\.jsp"
                    + "|listYear\\.do\\?menuNo=200755&mtgSe=A"
                    + "|statsPublictSchdul/listCldr\\.do\\?date="
                    + ").*");
        }
    }

    private static JsonNode firstTargetWithId(JsonNode targets, String targetId) {
        for (JsonNode target : targets) {
            if (targetId.equals(target.path("targetId").asText())) {
                return target;
            }
        }
        return null;
    }
}
