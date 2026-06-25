package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.PageRequest;
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
 *
 * 후보 쿼리 목록(단지명 기반)을 통째로 다시 모아도 안전하다 - 이미 캐시에 있는 건물은
 * findKnown()에서 걸러져 카카오를 다시 호출하지 않으므로, 매월 공공데이터가 갱신돼 신규
 * 건물이 섞여 들어와도 실질적으로는 그 신규 건물만 카카오에 추가로 질의하게 된다.
 */
@Service
public class RealEstateGeocodeBatchService {

    private static final Logger log = LoggerFactory.getLogger(RealEstateGeocodeBatchService.class);
    private static final int PAGE_SIZE = 2000;

    private final RealEstateGeocodeService geocodeService;
    private final KakaoGeocodeClient kakaoClient;
    private final RealEstateMarketFactRepository marketFactRepository;
    private final RealEstateGuNameLookup guNameLookup;
    private final ObjectMapper objectMapper;

    public RealEstateGeocodeBatchService(
            RealEstateGeocodeService geocodeService,
            KakaoGeocodeClient kakaoClient,
            RealEstateMarketFactRepository marketFactRepository,
            RealEstateGuNameLookup guNameLookup,
            ObjectMapper objectMapper
    ) {
        this.geocodeService = geocodeService;
        this.kakaoClient = kakaoClient;
        this.marketFactRepository = marketFactRepository;
        this.guNameLookup = guNameLookup;
        this.objectMapper = objectMapper;
    }

    /**
     * real_estate_market_facts에서 단지 주소 후보를 모아 사전 적재한다.
     * 이미 캐시된 건물은 자동으로 건너뛰므로, 매월 신규 건물만 추가되는 효과를 낸다.
     */
    public PreloadSummary preloadFromMarketFacts(int batchSize, long delayMillisBetweenBatches, int maxQueries) {
        Set<String> queries = collectCandidateQueries(maxQueries);
        log.info("geocode preload: {} distinct address queries collected (cap {})", queries.size(), maxQueries);
        return preload(queries, batchSize, delayMillisBetweenBatches);
    }

    private Set<String> collectCandidateQueries(int maxQueries) {
        Set<String> queries = new LinkedHashSet<>();
        int page = 0;
        while (queries.size() < maxQueries) {
            List<RealEstateMarketFactRepository.AddressProjection> rows = marketFactRepository.findAddressProjections(
                    PageRequest.of(page, PAGE_SIZE)
            );
            if (rows.isEmpty()) {
                break;
            }
            for (RealEstateMarketFactRepository.AddressProjection row : rows) {
                String query = toQuery(row);
                if (query != null) {
                    queries.add(query);
                }
                if (queries.size() >= maxQueries) {
                    break;
                }
            }
            page++;
        }
        return queries;
    }

    private String toQuery(RealEstateMarketFactRepository.AddressProjection row) {
        JsonNode valueJson = readJson(row.getValueJson());
        String apartmentName = textOrNull(valueJson.path("apartmentName"));
        if (apartmentName == null) {
            return null;
        }
        String legalDongName = textOrNull(valueJson.path("legalDongName"));
        String gu = guNameLookup.nameFor(row.getLegalDongCode());

        String query = String.join(" ", gu, legalDongName == null ? "" : legalDongName, apartmentName)
                .replaceAll("\\s+", " ")
                .trim();
        return query.isBlank() ? null : query;
    }

    private JsonNode readJson(String value) {
        try {
            return objectMapper.readTree(value);
        } catch (Exception e) {
            return objectMapper.getNodeFactory().objectNode();
        }
    }

    private static String textOrNull(JsonNode node) {
        return node.isMissingNode() || node.isNull() ? null : node.asText(null);
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
