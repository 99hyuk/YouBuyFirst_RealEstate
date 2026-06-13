package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateRegionImportRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateRegionImportResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketDataTargetResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetUpsertBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateTargetUpsertRequest;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Collection;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Objects;

@Service
public class RealEstateTargetService {

    private final RealEstateRegionRepository regionRepository;
    private final RealEstateTargetRepository targetRepository;
    private final RealEstateMarketDataTargetRepository marketDataTargetRepository;

    public RealEstateTargetService(
            RealEstateRegionRepository regionRepository,
            RealEstateTargetRepository targetRepository,
            RealEstateMarketDataTargetRepository marketDataTargetRepository
    ) {
        this.regionRepository = regionRepository;
        this.targetRepository = targetRepository;
        this.marketDataTargetRepository = marketDataTargetRepository;
    }

    @Transactional(readOnly = true)
    public List<RealEstateTargetResponse> search(String query, int limit) {
        int boundedLimit = Math.max(1, Math.min(limit, 100));
        String rawQuery = trimToNull(query);
        String lowerQuery = rawQuery == null ? null : rawQuery.toLowerCase(Locale.ROOT);
        String normalizedQuery = lowerQuery == null ? null : lowerQuery.replace(" ", "");
        return regionRepository.searchTargets(lowerQuery, normalizedQuery, rawQuery, PageRequest.of(0, boundedLimit));
    }

    @Transactional(readOnly = true)
    public List<RealEstateMarketDataTargetResponse> marketDataTargets(Boolean enabled, int limit) {
        int boundedLimit = Math.max(1, Math.min(limit, 500));
        return marketDataTargetRepository.listTargets(enabled, PageRequest.of(0, boundedLimit)).stream()
                .map(target -> new RealEstateMarketDataTargetResponse(
                        target.getTargetId(),
                        target.getProvider(),
                        target.getProviderDataset(),
                        target.getLawdCode(),
                        target.isEnabled(),
                        target.getRefreshIntervalHours(),
                        target.getStaleAfterHours()
                ))
                .toList();
    }

    @Transactional
    public RealEstateTargetUpsertBatchResponse upsertTargets(Collection<RealEstateTargetUpsertRequest> requests) {
        List<RealEstateTargetUpsertRequest> items = requests == null
                ? List.of()
                : requests.stream().filter(Objects::nonNull).toList();
        Instant now = Instant.now();
        int accepted = 0;
        int created = 0;
        int updated = 0;
        int skipped = 0;

        for (RealEstateTargetUpsertRequest item : items) {
            String targetId = requireText(item.targetId(), "targetId");
            String targetType = requireText(item.targetType(), "targetType").toLowerCase(Locale.ROOT);
            String displayName = requireText(item.displayName(), "displayName");
            String slug = defaultIfBlank(item.slug(), targetId);
            String reviewState = defaultIfBlank(item.reviewState(), "candidate").toLowerCase(Locale.ROOT);
            String dataStatus = defaultIfBlank(item.dataStatus(), "unknown").toLowerCase(Locale.ROOT);

            boolean[] isCreated = {false};
            RealEstateTarget target = targetRepository.findById(targetId)
                    .orElseGet(() -> {
                        isCreated[0] = true;
                        return new RealEstateTarget(
                                targetId,
                                targetType,
                                displayName,
                                slug,
                                reviewState,
                                dataStatus,
                                now
                        );
                    });
            if (!isCreated[0]) {
                target.update(targetType, displayName, slug, reviewState, dataStatus, now);
                updated++;
            } else {
                created++;
            }
            targetRepository.save(target);
            accepted++;
        }

        return new RealEstateTargetUpsertBatchResponse(accepted, created, updated, skipped);
    }

    @Transactional
    public RealEstateRegionImportResponse importRegions(Collection<RealEstateRegionImportRequest> requests) {
        List<RealEstateRegionImportRequest> items = requests == null
                ? List.of()
                : requests.stream()
                .filter(Objects::nonNull)
                .sorted(Comparator.comparingInt(item -> regionSortRank(item.regionLevel())))
                .toList();
        Instant now = Instant.now();
        int ensuredMarketDataTargets = 0;

        for (RealEstateRegionImportRequest item : items) {
            String targetId = requireText(item.targetId(), "targetId");
            String displayName = requireText(item.displayName(), "displayName");
            String regionLevel = requireText(item.regionLevel(), "regionLevel");
            String legalDongCode = trimToNull(item.legalDongCode());
            String slug = defaultIfBlank(item.slug(), targetId);
            String source = defaultIfBlank(item.source(), "import:unknown");

            RealEstateTarget target = targetRepository.findById(targetId)
                    .orElseGet(() -> new RealEstateTarget(
                            targetId,
                            "region",
                            displayName,
                            slug,
                            "approved",
                            "ok",
                            now
                    ));
            target.update("region", displayName, slug, "approved", "ok", now);
            targetRepository.save(target);

            RealEstateRegion region = regionRepository.findById(targetId)
                    .orElseGet(() -> new RealEstateRegion(
                            targetId,
                            regionLevel,
                            trimToNull(item.parentTargetId()),
                            legalDongCode,
                            trimToNull(item.regionCode()),
                            source
                    ));
            region.update(
                    regionLevel,
                    trimToNull(item.parentTargetId()),
                    legalDongCode,
                    trimToNull(item.regionCode()),
                    source
            );
            regionRepository.saveAndFlush(region);

            if ("sigungu".equals(regionLevel) && legalDongCode != null && legalDongCode.length() == 5) {
                ensuredMarketDataTargets += ensureMolitMarketDataTargets(targetId, legalDongCode, now);
            }
        }

        return new RealEstateRegionImportResponse(items.size(), ensuredMarketDataTargets);
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private int ensureMolitMarketDataTargets(String targetId, String lawdCode, Instant now) {
        int ensured = 0;
        for (String dataset : List.of("molit_apt_trade", "molit_apt_rent")) {
            RealEstateMarketDataTarget target = marketDataTargetRepository
                    .findByTargetIdAndProviderAndProviderDatasetAndLawdCode(targetId, "molit", dataset, lawdCode)
                    .orElseGet(() -> new RealEstateMarketDataTarget(
                            targetId,
                            "molit",
                            dataset,
                            lawdCode,
                            true,
                            24,
                            72,
                            now
                    ));
            target.update(true, 24, 72, now);
            marketDataTargetRepository.save(target);
            ensured++;
        }
        return ensured;
    }

    private static int regionSortRank(String regionLevel) {
        if ("sido".equals(regionLevel)) {
            return 0;
        }
        if ("sigungu".equals(regionLevel)) {
            return 1;
        }
        if ("eupmyeondong".equals(regionLevel)) {
            return 2;
        }
        return 3;
    }

    private static String requireText(String value, String fieldName) {
        String trimmed = trimToNull(value);
        if (trimmed == null) {
            throw new IllegalArgumentException(fieldName + " is required");
        }
        return trimmed;
    }

    private static String defaultIfBlank(String value, String fallback) {
        String trimmed = trimToNull(value);
        return trimmed == null ? fallback : trimmed;
    }
}
