package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.indicator.RealEstateReactionSnapshotRepository;
import com.youbuyfirst.backend.realestate.dto.RealEstateEvidenceItemRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateEvidenceItemResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateEvidenceLogBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateEvidenceLogRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateEvidenceLogResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Locale;

@Service
public class RealEstateEvidenceLogService {

    private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {
    };

    private final RealEstateEvidenceLogRepository evidenceLogRepository;
    private final RealEstateTargetRepository targetRepository;
    private final RealEstateReactionSnapshotRepository snapshotRepository;
    private final ObjectMapper objectMapper;

    public RealEstateEvidenceLogService(
            RealEstateEvidenceLogRepository evidenceLogRepository,
            RealEstateTargetRepository targetRepository,
            RealEstateReactionSnapshotRepository snapshotRepository,
            ObjectMapper objectMapper
    ) {
        this.evidenceLogRepository = evidenceLogRepository;
        this.targetRepository = targetRepository;
        this.snapshotRepository = snapshotRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public RealEstateEvidenceLogBatchResponse upsertAll(Collection<RealEstateEvidenceLogRequest> requests) {
        Instant now = Instant.now();
        int acceptedLogs = 0;
        int acceptedItems = 0;
        for (RealEstateEvidenceLogRequest request : requests) {
            String evidenceLogId = requireText(request.evidenceLogId(), "evidenceLogId");
            RealEstateTarget target = targetRepository.findById(requireText(request.targetId(), "targetId"))
                    .orElseThrow(() -> new ResponseStatusException(
                            HttpStatus.BAD_REQUEST,
                            "unknown real-estate target: " + request.targetId()
                    ));
            if (request.snapshotId() != null && !snapshotRepository.existsById(request.snapshotId())) {
                throw new ResponseStatusException(
                        HttpStatus.BAD_REQUEST,
                        "unknown real-estate reaction snapshot: " + request.snapshotId()
                );
            }
            List<RealEstateEvidenceLogItem> items = request.evidenceItems().stream()
                    .map(item -> toItem(item, now))
                    .toList();
            RealEstateEvidenceLog log = evidenceLogRepository.findById(evidenceLogId)
                    .orElseGet(() -> new RealEstateEvidenceLog(evidenceLogId, now));
            log.update(
                    target,
                    request.snapshotId(),
                    requireText(request.evaluationVersion(), "evaluationVersion"),
                    trimToNull(request.promptVersion()),
                    trimToNull(request.modelName()),
                    normalizeLower(requireText(request.tone(), "tone")),
                    requireText(request.summary(), "summary"),
                    trimToNull(request.subtitle()),
                    writeStringList(request.caveats() == null ? List.of() : request.caveats()),
                    normalizeLower(requireText(request.dataQuality(), "dataQuality")),
                    clampConfidence(request.confidence()),
                    trimToNull(request.skipReason()),
                    requireInstant(request.evaluatedAt(), "evaluatedAt"),
                    requireInstant(request.asOf(), "asOf"),
                    items,
                    now
            );
            evidenceLogRepository.save(log);
            acceptedLogs++;
            acceptedItems += items.size();
        }
        return new RealEstateEvidenceLogBatchResponse(acceptedLogs, acceptedItems);
    }

    @Transactional(readOnly = true)
    public List<RealEstateEvidenceLogResponse> listForTarget(String targetId, int limit) {
        int boundedLimit = Math.max(1, Math.min(limit, 100));
        targetRepository.findById(requireText(targetId, "targetId"))
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "unknown real-estate target: " + targetId
                ));
        return evidenceLogRepository.findByTarget_IdOrderByEvaluatedAtDescIdAsc(
                targetId,
                PageRequest.of(0, boundedLimit)
        ).stream().map(this::toResponse).toList();
    }

    private RealEstateEvidenceLogItem toItem(RealEstateEvidenceItemRequest request, Instant now) {
        return new RealEstateEvidenceLogItem(
                requireText(request.evidenceItemId(), "evidenceItemId"),
                normalizeLower(requireText(request.evidenceType(), "evidenceType")),
                normalizeLower(requireText(request.refType(), "refType")),
                requireText(request.refId(), "refId"),
                requireText(request.label(), "label"),
                trimToNull(request.valueText()),
                trimToNull(request.severity()) == null ? null : normalizeLower(request.severity()),
                now
        );
    }

    private RealEstateEvidenceLogResponse toResponse(RealEstateEvidenceLog log) {
        return new RealEstateEvidenceLogResponse(
                log.getId(),
                log.getTarget().getId(),
                log.getSnapshotId(),
                log.getEvaluationVersion(),
                log.getPromptVersion(),
                log.getModelName(),
                log.getTone(),
                log.getSummary(),
                log.getSubtitle(),
                readStringList(log.getCaveatsJson()),
                log.getDataQuality(),
                log.getConfidence(),
                log.getSkipReason(),
                log.getEvaluatedAt(),
                log.getAsOf(),
                log.getItems().stream().map(this::toItemResponse).toList()
        );
    }

    private RealEstateEvidenceItemResponse toItemResponse(RealEstateEvidenceLogItem item) {
        return new RealEstateEvidenceItemResponse(
                item.getId(),
                item.getEvidenceType(),
                item.getRefType(),
                item.getRefId(),
                item.getLabel(),
                item.getValueText(),
                item.getSeverity()
        );
    }

    private String writeStringList(List<String> values) {
        try {
            List<String> normalized = values.stream()
                    .map(RealEstateEvidenceLogService::trimToNull)
                    .filter(value -> value != null)
                    .toList();
            return objectMapper.writeValueAsString(normalized);
        } catch (JsonProcessingException exc) {
            throw new IllegalArgumentException("invalid evidence log caveats", exc);
        }
    }

    private List<String> readStringList(String value) {
        try {
            return objectMapper.readValue(value, STRING_LIST);
        } catch (JsonProcessingException exc) {
            throw new IllegalStateException("invalid stored evidence log caveats", exc);
        }
    }

    private static String requireText(String value, String fieldName) {
        String trimmed = trimToNull(value);
        if (trimmed == null) {
            throw new IllegalArgumentException(fieldName + " is required");
        }
        return trimmed;
    }

    private static Instant requireInstant(Instant value, String fieldName) {
        if (value == null) {
            throw new IllegalArgumentException(fieldName + " is required");
        }
        return value;
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static String normalizeLower(String value) {
        return value.trim().toLowerCase(Locale.ROOT);
    }

    private static Double clampConfidence(Double value) {
        if (value == null) {
            return null;
        }
        return Math.max(0.0, Math.min(1.0, value));
    }
}
