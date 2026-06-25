package com.youbuyfirst.backend.realestate;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/**
 * 공공데이터(MOLIT) 월간 갱신 직후, 신규 건물 좌표만 추가로 채우도록 사전 적재를
 * 다시 트리거하는 엔드포인트. 이미 캐시된 건물은 RealEstateGeocodeBatchService가
 * 자동으로 건너뛰므로 매번 전체 후보를 다시 모아도 실질적으로는 신규 건물만 카카오에 질의한다.
 * 카카오 호출에 시간이 걸릴 수 있어 백그라운드 스레드에서 돌리고 즉시 202를 반환한다.
 */
@RestController
public class RealEstateGeocodePreloadController {

    private static final Logger log = LoggerFactory.getLogger(RealEstateGeocodePreloadController.class);

    private final RealEstateGeocodeBatchService batchService;
    private final int batchSize;
    private final long delayMillisBetweenBatches;
    private final int maxQueries;

    public RealEstateGeocodePreloadController(
            RealEstateGeocodeBatchService batchService,
            @Value("${app.realestate.geocode.preload.batch-size:8}") int batchSize,
            @Value("${app.realestate.geocode.preload.delay-ms:1100}") long delayMillisBetweenBatches,
            @Value("${app.realestate.geocode.preload.max-queries:20000}") int maxQueries
    ) {
        this.batchService = batchService;
        this.batchSize = batchSize;
        this.delayMillisBetweenBatches = delayMillisBetweenBatches;
        this.maxQueries = maxQueries;
    }

    @PostMapping("/api/realestate/geocode/preload")
    @ResponseStatus(HttpStatus.ACCEPTED)
    public void triggerPreload() {
        log.info("geocode preload triggered via API (incremental - already-cached buildings are skipped)");
        Thread.ofVirtual().start(() -> {
            RealEstateGeocodeBatchService.PreloadSummary summary =
                    batchService.preloadFromMarketFacts(batchSize, delayMillisBetweenBatches, maxQueries);
            log.info(
                    "geocode preload (API-triggered) done: total={}, alreadyCached={}, newlyResolved={}, failed={}",
                    summary.totalQueries(), summary.alreadyCached(), summary.newlyResolved(), summary.failed()
            );
        });
    }
}
