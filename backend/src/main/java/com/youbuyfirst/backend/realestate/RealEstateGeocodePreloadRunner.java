package com.youbuyfirst.backend.realestate;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.util.Arrays;

/**
 * 서비스 오픈 전(또는 대량 신규 지역 유입 전) 한 번 돌리는 사전 적재 배치.
 * 다음 두 경우에 동작한다.
 *  1) 실행 인자에 --geocode-preload 가 있는 경우 (수동 트리거)
 *  2) 지오코딩 캐시 테이블(real_estate_geocode)이 비어 있는 경우 (최초 기동 시 자동 트리거)
 *
 * 매월 공공데이터가 갱신돼 신규 건물이 들어와도, 이미 캐시된 건물은 RealEstateGeocodeBatchService가
 * 자동으로 건너뛰므로 매번 전체를 다시 모아도 실질적으로는 신규 건물만 카카오에 추가 질의한다.
 * (앱 기동과 무관하게 주기적으로 다시 돌리려면 {@link RealEstateGeocodePreloadController} 참고.)
 *
 * 예) java -jar app.jar --geocode-preload
 */
@Component
public class RealEstateGeocodePreloadRunner implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(RealEstateGeocodePreloadRunner.class);
    private static final String TRIGGER_ARG = "--geocode-preload";

    private final RealEstateGeocodeRepository geocodeRepository;
    private final RealEstateGeocodeBatchService batchService;

    private final int batchSize;
    private final long delayMillisBetweenBatches;
    private final int maxQueries;

    public RealEstateGeocodePreloadRunner(
            RealEstateGeocodeRepository geocodeRepository,
            RealEstateGeocodeBatchService batchService,
            @Value("${app.realestate.geocode.preload.batch-size:8}") int batchSize,
            @Value("${app.realestate.geocode.preload.delay-ms:1100}") long delayMillisBetweenBatches,
            @Value("${app.realestate.geocode.preload.max-queries:20000}") int maxQueries
    ) {
        this.geocodeRepository = geocodeRepository;
        this.batchService = batchService;
        this.batchSize = batchSize;
        this.delayMillisBetweenBatches = delayMillisBetweenBatches;
        this.maxQueries = maxQueries;
    }

    @Override
    public void run(String... args) {
        boolean explicitlyTriggered = Arrays.asList(args).contains(TRIGGER_ARG);
        if (!explicitlyTriggered && geocodeRepository.count() > 0) {
            return;
        }

        if (explicitlyTriggered) {
            log.info("geocode preload triggered manually via {}", TRIGGER_ARG);
        } else {
            log.info("geocode cache table is empty, triggering preload automatically");
        }

        RealEstateGeocodeBatchService.PreloadSummary summary =
                batchService.preloadFromMarketFacts(batchSize, delayMillisBetweenBatches, maxQueries);
        log.info(
                "geocode preload done: total={}, alreadyCached={}, newlyResolved={}, failed={}",
                summary.totalQueries(), summary.alreadyCached(), summary.newlyResolved(), summary.failed()
        );
    }
}
