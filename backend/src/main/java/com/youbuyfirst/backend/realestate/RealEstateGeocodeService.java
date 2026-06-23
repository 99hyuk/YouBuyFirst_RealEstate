package com.youbuyfirst.backend.realestate;

import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * 단지 검색 문자열을 좌표로 일괄 해석한다. DB 캐시를 먼저 보고, 미캐시 건만 카카오에
 * (병렬로) 질의해 저장하므로 같은 단지는 다음부터 외부 호출 없이 즉시 반환된다.
 */
@Service
public class RealEstateGeocodeService {

    private static final int MAX_QUERIES = 800;
    private static final int MAX_PARALLELISM = 8;

    private final RealEstateGeocodeRepository repository;
    private final KakaoGeocodeClient kakaoClient;

    public RealEstateGeocodeService(RealEstateGeocodeRepository repository, KakaoGeocodeClient kakaoClient) {
        this.repository = repository;
        this.kakaoClient = kakaoClient;
    }

    public List<GeocodeResult> resolve(List<String> queries) {
        if (queries == null || queries.isEmpty()) {
            return List.of();
        }
        List<String> distinct = queries.stream()
                .filter(q -> q != null && !q.isBlank())
                .map(String::trim)
                .distinct()
                .limit(MAX_QUERIES)
                .toList();
        if (distinct.isEmpty()) {
            return List.of();
        }

        Map<String, RealEstateGeocode> known = repository.findByQueryKeyIn(distinct).stream()
                .collect(Collectors.toMap(RealEstateGeocode::getQueryKey, Function.identity(), (a, b) -> a));

        List<String> misses = distinct.stream()
                .filter(query -> !known.containsKey(query))
                .toList();

        if (!misses.isEmpty() && kakaoClient.isEnabled()) {
            Instant now = Instant.now();
            List<RealEstateGeocode> resolved = geocodeInParallel(misses, now);
            repository.saveAll(resolved);
            for (RealEstateGeocode entity : resolved) {
                known.put(entity.getQueryKey(), entity);
            }
        }

        List<GeocodeResult> results = new ArrayList<>();
        for (String query : distinct) {
            RealEstateGeocode entity = known.get(query);
            if (entity != null && entity.isResolved() && entity.getLat() != null && entity.getLng() != null) {
                results.add(new GeocodeResult(query, entity.getLat(), entity.getLng()));
            }
        }
        return results;
    }

    private List<RealEstateGeocode> geocodeInParallel(List<String> misses, Instant now) {
        int parallelism = Math.min(MAX_PARALLELISM, misses.size());
        ExecutorService pool = Executors.newFixedThreadPool(parallelism);
        try {
            List<CompletableFuture<RealEstateGeocode>> futures = misses.stream()
                    .map(query -> CompletableFuture.supplyAsync(() -> toEntity(query, now), pool))
                    .toList();
            return futures.stream().map(CompletableFuture::join).toList();
        } finally {
            pool.shutdown();
        }
    }

    private RealEstateGeocode toEntity(String query, Instant now) {
        Optional<double[]> coordinate = kakaoClient.geocode(query);
        return coordinate
                .map(c -> new RealEstateGeocode(query, c[0], c[1], true, now))
                .orElseGet(() -> new RealEstateGeocode(query, null, null, false, now));
    }

    public record GeocodeResult(String query, double lat, double lng) {
    }
}
