package com.youbuyfirst.backend.realestate;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.Collection;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 대량의 단지 주소를 사전 지오코딩해 DB 캐시에 밀어 넣는 배치 전용 서비스.
 * {@link RealEstateGeocodeService}의 DB 우선 조회/Write-Through 저장 로직을 그대로 재사용하고,
 * 카카오 API 일일/초당 호출 제한을 지키기 위해 미스 건만 작은 슬라이스로 나눠 호출 사이에 지연을 둔다.
 */
@Service
public class RealEstateGeocodeBatchService {

    private static final Logger log = LoggerFactory.getLogger(RealEstateGeocodeBatchService.class);

    private final RealEstateGeocodeService geocodeService;
    private final KakaoGeocodeClient kakaoClient;

    public RealEstateGeocodeBatchService(RealEstateGeocodeService geocodeService, KakaoGeocodeClient kakaoClient) {
        this.geocodeService = geocodeService;
        this.kakaoClient = kakaoClient;
    }

    public PreloadSummary preload(Collection<String> queries, int batchSize, long delayMillisBetweenBatches) {
        List<String> distinct = dedupe(queries);
        if (distinct.isEmpty()) {
            return new PreloadSummary(0, 0, 0, 0);
        }
        if (!kakaoClient.isEnabled()) {
            log.warn("kakao geocode client is disabled (no REST key) - skipping preload of {} queries", distinct.size());
            return new PreloadSummary(distinct.size(), 0, 0, distinct.size());
        }

        Map<String, RealEstateGeocode> known = geocodeService.findKnown(distinct);
        List<String> misses = distinct.stream().filter(query -> !known.containsKey(query)).toList();

        int resolved = 0;
        int failed = 0;
        int boundedBatchSize = Math.max(1, batchSize);
        int totalSlices = (misses.size() + boundedBatchSize - 1) / boundedBatchSize;

        for (int sliceIndex = 0; sliceIndex < totalSlices; sliceIndex++) {
            int from = sliceIndex * boundedBatchSize;
            int to = Math.min(from + boundedBatchSize, misses.size());
            List<String> slice = misses.subList(from, to);

            List<RealEstateGeocode> entities = geocodeService.geocodeAndSave(slice);
            for (RealEstateGeocode entity : entities) {
                if (entity.isResolved()) {
                    resolved++;
                } else {
                    failed++;
                }
            }
            log.info(
                    "geocode preload progress: {}/{} slices done ({} resolved, {} failed so far)",
                    sliceIndex + 1, totalSlices, resolved, failed
            );

            boolean isLastSlice = sliceIndex == totalSlices - 1;
            if (!isLastSlice && delayMillisBetweenBatches > 0) {
                sleep(delayMillisBetweenBatches);
            }
        }

        return new PreloadSummary(distinct.size(), known.size(), resolved, failed);
    }

    private static List<String> dedupe(Collection<String> queries) {
        Set<String> distinct = new LinkedHashSet<>();
        for (String query : queries) {
            if (query != null && !query.isBlank()) {
                distinct.add(query.trim());
            }
        }
        return distinct.stream().toList();
    }

    private static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public record PreloadSummary(int totalQueries, int alreadyCached, int newlyResolved, int failed) {
    }
}
