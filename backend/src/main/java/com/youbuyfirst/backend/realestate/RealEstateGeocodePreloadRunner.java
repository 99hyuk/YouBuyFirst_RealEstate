package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * 서비스 오픈 전(또는 대량 신규 지역 유입 전) 한 번 돌리는 사전 적재 배치.
 * 다음 두 경우에 동작한다.
 *  1) 실행 인자에 --geocode-preload 가 있는 경우 (수동 트리거)
 *  2) 지오코딩 캐시 테이블(real_estate_geocode)이 비어 있는 경우 (최초 기동 시 자동 트리거)
 *
 * 예) java -jar app.jar --geocode-preload
 */
@Component
public class RealEstateGeocodePreloadRunner implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(RealEstateGeocodePreloadRunner.class);
    private static final String TRIGGER_ARG = "--geocode-preload";
    private static final int PAGE_SIZE = 2000;

    private final RealEstateMarketFactRepository marketFactRepository;
    private final RealEstateGeocodeRepository geocodeRepository;
    private final RealEstateGuNameLookup guNameLookup;
    private final RealEstateGeocodeBatchService batchService;
    private final ObjectMapper objectMapper;

    private final int batchSize;
    private final long delayMillisBetweenBatches;
    private final int maxQueries;

    public RealEstateGeocodePreloadRunner(
            RealEstateMarketFactRepository marketFactRepository,
            RealEstateGeocodeRepository geocodeRepository,
            RealEstateGuNameLookup guNameLookup,
            RealEstateGeocodeBatchService batchService,
            ObjectMapper objectMapper,
            @Value("${app.realestate.geocode.preload.batch-size:8}") int batchSize,
            @Value("${app.realestate.geocode.preload.delay-ms:1100}") long delayMillisBetweenBatches,
            @Value("${app.realestate.geocode.preload.max-queries:20000}") int maxQueries
    ) {
        this.marketFactRepository = marketFactRepository;
        this.geocodeRepository = geocodeRepository;
        this.guNameLookup = guNameLookup;
        this.batchService = batchService;
        this.objectMapper = objectMapper;
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

        log.info("geocode preload triggered: collecting candidate addresses (max {})", maxQueries);
        Set<String> queries = collectCandidateQueries();
        log.info("geocode preload: {} distinct address queries collected, calling kakao for cache misses", queries.size());

        RealEstateGeocodeBatchService.PreloadSummary summary = batchService.preload(queries, batchSize, delayMillisBetweenBatches);
        log.info(
                "geocode preload done: total={}, alreadyCached={}, newlyResolved={}, failed={}",
                summary.totalQueries(), summary.alreadyCached(), summary.newlyResolved(), summary.failed()
        );
    }

    private Set<String> collectCandidateQueries() {
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
}
