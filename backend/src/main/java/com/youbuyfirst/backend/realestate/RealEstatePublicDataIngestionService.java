package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketFactRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateMarketFactStagingRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataImportRunResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataPromoteRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataPromoteResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataRawIngestionBatchRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataRawIngestionResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataRawItemRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstatePublicDataRunRequest;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.LocalDate;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;

@Service
public class RealEstatePublicDataIngestionService {

    private final RealEstatePublicDataImportRunRepository runRepository;
    private final RealEstatePublicDataRawItemRepository rawItemRepository;
    private final RealEstateMarketFactStagingRepository stagingRepository;
    private final RealEstateMarketFactService marketFactService;
    private final ObjectMapper objectMapper;

    public RealEstatePublicDataIngestionService(
            RealEstatePublicDataImportRunRepository runRepository,
            RealEstatePublicDataRawItemRepository rawItemRepository,
            RealEstateMarketFactStagingRepository stagingRepository,
            RealEstateMarketFactService marketFactService,
            ObjectMapper objectMapper
    ) {
        this.runRepository = runRepository;
        this.rawItemRepository = rawItemRepository;
        this.stagingRepository = stagingRepository;
        this.marketFactService = marketFactService;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public RealEstatePublicDataRawIngestionResponse ingest(RealEstatePublicDataRawIngestionBatchRequest request) {
        Instant now = Instant.now();
        RealEstatePublicDataRunRequest runRequest = request.run();
        String providerDataset = normalizeLower(runRequest.providerDataset());
        RealEstatePublicDataImportRun run = runRepository.findByRunKey(runRequest.runKey().trim())
                .orElseGet(() -> new RealEstatePublicDataImportRun(runRequest.runKey().trim()));
        int acceptedRawItems = 0;
        int acceptedStagingItems = 0;
        run.update(
                providerDataset,
                normalizeLower(runRequest.runType()),
                runRequest.requestedFrom(),
                runRequest.requestedTo(),
                writeJson(runRequest.requestParams()),
                normalizeLower(runRequest.status()),
                request.items().size(),
                0,
                0,
                runRequest.startedAt(),
                runRequest.finishedAt(),
                trimToNull(runRequest.errorMessage()),
                now
        );
        run = runRepository.save(run);

        for (RealEstatePublicDataRawItemRequest itemRequest : request.items()) {
            String itemProviderDataset = normalizeLowerOrDefault(itemRequest.providerDataset(), providerDataset);
            String providerObjectId = itemRequest.providerObjectId().trim();
            String rawPayloadJson = writeJson(itemRequest.rawPayload());
            RealEstatePublicDataRawItem rawItem = rawItemRepository
                    .findByProviderDatasetAndProviderObjectId(itemProviderDataset, providerObjectId)
                    .orElseGet(() -> new RealEstatePublicDataRawItem(itemProviderDataset, providerObjectId));
            rawItem.update(
                    run.getId(),
                    trimToNull(itemRequest.legalDongCode()),
                    trimToNull(itemRequest.targetId()),
                    itemRequest.observedAt(),
                    itemRequest.asOf(),
                    itemRequest.sourceUpdatedAt(),
                    sha256Hex(rawPayloadJson),
                    rawPayloadJson,
                    normalizeLower(itemRequest.landingStatus()),
                    now
            );
            rawItem = rawItemRepository.save(rawItem);
            acceptedRawItems++;

            if (itemRequest.staging() != null) {
                upsertStaging(rawItem.getId(), itemProviderDataset, providerObjectId, itemRequest.staging(), now);
                acceptedStagingItems++;
            }
        }

        run.update(
                providerDataset,
                normalizeLower(runRequest.runType()),
                runRequest.requestedFrom(),
                runRequest.requestedTo(),
                writeJson(runRequest.requestParams()),
                normalizeLower(runRequest.status()),
                request.items().size(),
                acceptedRawItems,
                acceptedStagingItems,
                runRequest.startedAt(),
                runRequest.finishedAt(),
                trimToNull(runRequest.errorMessage()),
                now
        );
        run = runRepository.save(run);
        return new RealEstatePublicDataRawIngestionResponse(run.getId(), acceptedRawItems, acceptedStagingItems);
    }

    @Transactional(readOnly = true)
    public List<RealEstatePublicDataImportRunResponse> listRuns(
            String providerDataset,
            String status,
            List<String> runKeys,
            int limit
    ) {
        String normalizedProviderDataset = trimToNull(providerDataset) == null ? null : normalizeLower(providerDataset);
        String normalizedStatus = trimToNull(status) == null ? null : normalizeLower(status);
        List<String> normalizedRunKeys = runKeys == null
                ? List.of()
                : runKeys.stream()
                .map(RealEstatePublicDataIngestionService::trimToNull)
                .filter(value -> value != null)
                .distinct()
                .toList();
        if (!normalizedRunKeys.isEmpty()) {
            return runRepository.searchByRunKeys(
                    normalizedRunKeys,
                    normalizedProviderDataset,
                    normalizedStatus
            ).stream().map(this::toResponse).toList();
        }

        int boundedLimit = Math.max(1, Math.min(limit, 500));
        return runRepository.search(
                normalizedProviderDataset,
                normalizedStatus,
                PageRequest.of(0, boundedLimit)
        ).stream().map(this::toResponse).toList();
    }

    @Transactional
    public RealEstatePublicDataPromoteResponse promoteStaging(RealEstatePublicDataPromoteRequest request) {
        Instant now = Instant.now();
        int boundedLimit = request.limit() == null ? 1_000 : Math.max(1, Math.min(request.limit(), 10_000));
        String providerDataset = trimToNull(request.providerDataset()) == null
                ? null
                : normalizeLower(request.providerDataset());
        String runKey = trimToNull(request.runKey());
        String validationStatus = trimToNull(request.validationStatus()) == null
                ? "valid"
                : normalizeLower(request.validationStatus());
        List<RealEstateMarketFactRequest> marketFactRequests = stagingRepository.searchPromotable(
                providerDataset,
                runKey,
                validationStatus,
                PageRequest.of(0, boundedLimit)
        ).stream().map(staging -> toMarketFactRequest(staging, now)).toList();
        int promotedFacts = marketFactService.upsertAll(marketFactRequests);

        if (runKey != null) {
            runRepository.findByRunKey(runKey).ifPresent(run -> {
                run.markPromoted(promotedFacts, now);
                runRepository.save(run);
            });
        }
        return new RealEstatePublicDataPromoteResponse(promotedFacts);
    }

    private void upsertStaging(
            Long rawItemId,
            String providerDataset,
            String providerObjectId,
            RealEstateMarketFactStagingRequest request,
            Instant now
    ) {
        RealEstateMarketFactStaging staging = stagingRepository.findByRawItemId(rawItemId)
                .orElseGet(() -> new RealEstateMarketFactStaging(rawItemId));
        staging.update(
                providerDataset,
                providerObjectId,
                normalizeLower(request.targetType()),
                trimToNull(request.targetId()),
                trimToNull(request.legalDongCode()),
                normalizeLower(request.factType()),
                request.observedAt(),
                request.asOf(),
                writeJson(request.valueJson()),
                normalizeLower(request.validationStatus()),
                trimToNull(request.validationMessage()),
                now
        );
        stagingRepository.save(staging);
    }

    private RealEstateMarketFactRequest toMarketFactRequest(RealEstateMarketFactStaging staging, Instant now) {
        LocalDate observedAt = staging.getObservedAt() == null ? staging.getAsOf() : staging.getObservedAt();
        return new RealEstateMarketFactRequest(
                staging.getTargetType(),
                staging.getTargetId(),
                staging.getFactType(),
                providerFromDataset(staging.getProviderDataset()),
                staging.getProviderDataset(),
                staging.getProviderObjectId(),
                staging.getLegalDongCode(),
                observedAt,
                staging.getAsOf(),
                now,
                null,
                readJson(staging.getValueJson()),
                dataStatusFromValidation(staging.getValidationStatus()),
                false
        );
    }

    private RealEstatePublicDataImportRunResponse toResponse(RealEstatePublicDataImportRun run) {
        return new RealEstatePublicDataImportRunResponse(
                run.getId(),
                run.getRunKey(),
                run.getProviderDataset(),
                run.getRunType(),
                run.getRequestedFrom(),
                run.getRequestedTo(),
                run.getStatus(),
                run.getRowsSeen(),
                run.getRowsLanded(),
                run.getRowsStaged(),
                run.getRowsPromoted(),
                run.getStartedAt(),
                run.getFinishedAt(),
                run.getErrorMessage()
        );
    }

    private String writeJson(JsonNode value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (JsonProcessingException exc) {
            throw new IllegalArgumentException("invalid public data JSON payload", exc);
        }
    }

    private JsonNode readJson(String value) {
        try {
            return objectMapper.readTree(value);
        } catch (JsonProcessingException exc) {
            throw new IllegalStateException("invalid staged public data JSON payload", exc);
        }
    }

    private static String sha256Hex(String value) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(value.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException exc) {
            throw new IllegalStateException("SHA-256 is not available", exc);
        }
    }

    private static String normalizeLower(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
    }

    private static String normalizeLowerOrDefault(String value, String defaultValue) {
        String normalized = normalizeLower(value);
        return normalized.isBlank() ? defaultValue : normalized;
    }

    private static String providerFromDataset(String providerDataset) {
        String normalized = normalizeLower(providerDataset);
        int separatorIndex = normalized.indexOf('_');
        if (separatorIndex <= 0) {
            return normalized;
        }
        return normalized.substring(0, separatorIndex);
    }

    private static String dataStatusFromValidation(String validationStatus) {
        String normalized = normalizeLower(validationStatus);
        if ("valid".equals(normalized)) {
            return "ok";
        }
        return normalized;
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }
}
