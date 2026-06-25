package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.realestate.dto.RealEstateRegionalReportBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateRegionalReportRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateRegionalReportResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateRegionalReportSourceRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateRegionalReportSourceResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Locale;

@Service
public class RealEstateRegionalReportService {

    private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {
    };

    private final RealEstateRegionalReportRepository reportRepository;
    private final RealEstateTargetRepository targetRepository;
    private final RealEstateRegionRepository regionRepository;
    private final ObjectMapper objectMapper;

    public RealEstateRegionalReportService(
            RealEstateRegionalReportRepository reportRepository,
            RealEstateTargetRepository targetRepository,
            RealEstateRegionRepository regionRepository,
            ObjectMapper objectMapper
    ) {
        this.reportRepository = reportRepository;
        this.targetRepository = targetRepository;
        this.regionRepository = regionRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public RealEstateRegionalReportBatchResponse upsertAll(Collection<RealEstateRegionalReportRequest> requests) {
        Instant now = Instant.now();
        int acceptedReports = 0;
        int acceptedSources = 0;
        for (RealEstateRegionalReportRequest request : requests == null ? List.<RealEstateRegionalReportRequest>of() : requests) {
            RealEstateTarget target = targetRepository.findById(requireText(request.targetId(), "targetId"))
                    .orElseThrow(() -> new ResponseStatusException(
                            HttpStatus.BAD_REQUEST,
                            "unknown real-estate target: " + request.targetId()
                    ));
            List<RealEstateRegionalReportSource> sources = toSources(target.getId(), request.sources(), now);
            RealEstateRegionalReport report = reportRepository.findById(target.getId())
                    .orElseGet(() -> new RealEstateRegionalReport(target.getId(), now));
            report.update(
                    target,
                    requireText(request.reportId(), "reportId"),
                    requireText(request.reportVersion(), "reportVersion"),
                    trimToNull(request.promptVersion()),
                    trimToNull(request.modelName()),
                    requireText(request.generatedBy(), "generatedBy"),
                    requireText(request.title(), "title"),
                    requireText(request.headline(), "headline"),
                    requireText(request.summary(), "summary"),
                    requireText(request.body(), "body"),
                    writeStringList(request.expectationPoints()),
                    writeStringList(request.concernPoints()),
                    normalizeLower(requireText(request.dataQuality(), "dataQuality")),
                    clampConfidence(request.confidence()),
                    requireInstant(request.asOf(), "asOf"),
                    requireInstant(request.publishedAt(), "publishedAt"),
                    sources,
                    now
            );
            reportRepository.save(report);
            acceptedReports++;
            acceptedSources += sources.size();
        }
        return new RealEstateRegionalReportBatchResponse(acceptedReports, acceptedSources);
    }

    @Transactional(readOnly = true)
    public RealEstateRegionalReportResponse latestForTarget(String targetId) {
        String normalizedTargetId = requireText(targetId, "targetId");
        targetRepository.findById(normalizedTargetId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "unknown real-estate target: " + normalizedTargetId
                ));
        RealEstateRegionalReport report = reportRepository.findById(normalizedTargetId)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND,
                        "regional report is not ready for target: " + normalizedTargetId
                ));
        return toResponse(report);
    }

    private List<RealEstateRegionalReportSource> toSources(
            String targetId,
            List<RealEstateRegionalReportSourceRequest> requests,
            Instant now
    ) {
        List<RealEstateRegionalReportSourceRequest> safeRequests = requests == null ? List.of() : requests;
        return java.util.stream.IntStream.range(0, safeRequests.size())
                .mapToObj(index -> toSource(targetId, safeRequests.get(index), index + 1, now))
                .toList();
    }

    private RealEstateRegionalReportSource toSource(
            String targetId,
            RealEstateRegionalReportSourceRequest request,
            int displayOrder,
            Instant now
    ) {
        return new RealEstateRegionalReportSource(
                defaultIfBlank(request.reportSourceId(), "regional-report-source-%s-%02d".formatted(targetId, displayOrder)),
                displayOrder,
                normalizeLower(requireText(request.refType(), "refType")),
                trimToNull(request.refId()),
                requireText(request.label(), "label"),
                requireText(request.title(), "title"),
                trimToNull(request.url()),
                trimToNull(request.sourceName()),
                request.publishedAt(),
                normalizeLower(requireText(request.dataStatus(), "dataStatus")),
                now
        );
    }

    private RealEstateRegionalReportResponse toResponse(RealEstateRegionalReport report) {
        RealEstateRegion region = regionRepository.findById(report.getTargetId()).orElse(null);
        RealEstateTarget target = report.getTarget();
        return new RealEstateRegionalReportResponse(
                report.getReportId(),
                report.getTargetId(),
                target == null ? report.getTargetId() : target.getDisplayName(),
                region == null ? null : region.getRegionLevel(),
                region == null ? null : region.getRegionCode(),
                report.getReportVersion(),
                report.getPromptVersion(),
                report.getModelName(),
                report.getGeneratedBy(),
                report.getTitle(),
                report.getHeadline(),
                report.getSummary(),
                report.getBody(),
                readStringList(report.getExpectationPointsJson()),
                readStringList(report.getConcernPointsJson()),
                report.getDataQuality(),
                report.getConfidence(),
                report.getAsOf(),
                report.getPublishedAt(),
                report.getSources().stream().map(this::toSourceResponse).toList()
        );
    }

    private RealEstateRegionalReportSourceResponse toSourceResponse(RealEstateRegionalReportSource source) {
        return new RealEstateRegionalReportSourceResponse(
                source.getId(),
                source.getDisplayOrder(),
                source.getRefType(),
                source.getRefId(),
                source.getLabel(),
                source.getTitle(),
                source.getUrl(),
                source.getSourceName(),
                source.getPublishedAt(),
                source.getDataStatus()
        );
    }

    private String writeStringList(List<String> values) {
        try {
            List<String> normalized = (values == null ? List.<String>of() : values).stream()
                    .map(RealEstateRegionalReportService::trimToNull)
                    .filter(value -> value != null)
                    .toList();
            return objectMapper.writeValueAsString(normalized);
        } catch (JsonProcessingException exc) {
            throw new IllegalArgumentException("invalid regional report points", exc);
        }
    }

    private List<String> readStringList(String value) {
        try {
            return objectMapper.readValue(value, STRING_LIST);
        } catch (JsonProcessingException exc) {
            throw new IllegalStateException("invalid stored regional report points", exc);
        }
    }

    private static Instant requireInstant(Instant value, String fieldName) {
        if (value == null) {
            throw new IllegalArgumentException(fieldName + " is required");
        }
        return value;
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
