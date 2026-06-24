package com.youbuyfirst.backend.realestate;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.youbuyfirst.backend.realestate.dto.RealEstateDailyBriefingBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateDailyBriefingRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateDailyBriefingResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateDailyBriefingSectionRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateDailyBriefingSectionResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateDailyBriefingSourceItemRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateDailyBriefingSourceItemResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;

@Service
public class RealEstateDailyBriefingService {

    private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {
    };
    private static final TypeReference<List<Map<String, Object>>> MAP_LIST = new TypeReference<>() {
    };
    private static final List<String> REQUIRED_SECTION_TITLES = List.of(
            "오늘의 핵심 흐름",
            "주목할 지역과 이유",
            "시장 변수",
            "관련 뉴스·리포트"
    );
    private static final List<String> FORBIDDEN_TIME_LABELS = List.of(
            "24시간",
            "7일",
            "1개월",
            "3개월"
    );
    private static final List<String> FORBIDDEN_ACTION_COPY = List.of(
            "사라",
            "팔아라",
            "청약 넣어라",
            "지금 들어가라",
            "오른다",
            "수익 보장",
            "확정 호재",
            "대출 받아라",
            "매수 기회",
            "매도 신호"
    );

    private final RealEstateDailyBriefingRepository repository;
    private final ObjectMapper objectMapper;

    public RealEstateDailyBriefingService(
            RealEstateDailyBriefingRepository repository,
            ObjectMapper objectMapper
    ) {
        this.repository = repository;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public RealEstateDailyBriefingBatchResponse upsertAll(Collection<RealEstateDailyBriefingRequest> requests) {
        Instant now = Instant.now();
        int acceptedBriefings = 0;
        int acceptedSections = 0;
        int acceptedSourceItems = 0;
        for (RealEstateDailyBriefingRequest request : requests) {
            validate(request);
            String briefingId = requireText(request.briefingId(), "briefingId");
            List<RealEstateDailyBriefingSection> sections = indexedSections(request, now);
            List<RealEstateDailyBriefingSourceItem> sourceItems = indexedSourceItems(request, now);
            RealEstateDailyBriefing briefing = repository.findById(briefingId)
                    .orElseGet(() -> new RealEstateDailyBriefing(briefingId, now));
            briefing.update(
                    request.briefingDate(),
                    requireText(request.title(), "title"),
                    writeStringList(normalizedHeadlines(request.summaryHeadlines())),
                    writeMapList(request.focusRegions() == null ? List.of() : request.focusRegions()),
                    trimToNull(request.modelName()),
                    trimToNull(request.promptVersion()),
                    requireInstant(request.generatedAt(), "generatedAt"),
                    sections,
                    sourceItems,
                    now
            );
            repository.save(briefing);
            acceptedBriefings++;
            acceptedSections += sections.size();
            acceptedSourceItems += sourceItems.size();
        }
        return new RealEstateDailyBriefingBatchResponse(acceptedBriefings, acceptedSections, acceptedSourceItems);
    }

    @Transactional(readOnly = true)
    public Optional<RealEstateDailyBriefingResponse> latest() {
        return repository.findFirstByOrderByGeneratedAtDescIdDesc().map(this::toResponse);
    }

    private List<RealEstateDailyBriefingSection> indexedSections(RealEstateDailyBriefingRequest request, Instant now) {
        return request.sections().stream()
                .map(section -> toSection(request.briefingId(), section, now))
                .toList();
    }

    private RealEstateDailyBriefingSection toSection(
            String briefingId,
            RealEstateDailyBriefingSectionRequest request,
            Instant now
    ) {
        int displayOrder = request.displayOrder() == null ? 100 : request.displayOrder();
        String sectionId = requireText(request.sectionId(), "sectionId");
        return new RealEstateDailyBriefingSection(
                briefingId + ":" + sectionId,
                sectionId,
                requireText(request.title(), "section.title"),
                requireText(request.body(), "section.body"),
                displayOrder,
                now
        );
    }

    private List<RealEstateDailyBriefingSourceItem> indexedSourceItems(RealEstateDailyBriefingRequest request, Instant now) {
        return request.sourceItems().stream()
                .map(sourceItem -> toSourceItem(request.briefingId(), sourceItem, now))
                .toList();
    }

    private RealEstateDailyBriefingSourceItem toSourceItem(
            String briefingId,
            RealEstateDailyBriefingSourceItemRequest request,
            Instant now
    ) {
        int displayOrder = request.displayOrder() == null ? 100 : request.displayOrder();
        return new RealEstateDailyBriefingSourceItem(
                briefingId + ":" + requireText(request.sourceItemId(), "sourceItemId"),
                requireText(request.sourceType(), "sourceType"),
                trimToNull(request.refId()),
                trimToNull(request.label()),
                requireText(request.title(), "sourceItem.title"),
                trimToNull(request.url()),
                displayOrder,
                now
        );
    }

    private void validate(RealEstateDailyBriefingRequest request) {
        if (request.summaryHeadlines() == null || normalizedHeadlines(request.summaryHeadlines()).size() != 3) {
            throw badRequest("daily briefing requires exactly three summaryHeadlines");
        }
        if (request.sections() == null || request.sections().isEmpty()) {
            throw badRequest("daily briefing requires sections");
        }
        List<String> titles = request.sections().stream()
                .map(RealEstateDailyBriefingSectionRequest::title)
                .map(RealEstateDailyBriefingService::trimToNull)
                .filter(title -> title != null)
                .toList();
        if (!titles.containsAll(REQUIRED_SECTION_TITLES)) {
            throw badRequest("daily briefing requires narrative section titles");
        }
        validateCopy(request.title());
        request.summaryHeadlines().forEach(this::validateCopy);
        request.sections().forEach(section -> {
            validateCopy(section.title());
            validateCopy(section.body());
        });
    }

    private void validateCopy(String value) {
        String normalized = trimToNull(value);
        if (normalized == null) {
            return;
        }
        String lowered = normalized.toLowerCase(Locale.ROOT);
        boolean hasForbiddenTimeLabel = FORBIDDEN_TIME_LABELS.stream().anyMatch(lowered::contains);
        if (hasForbiddenTimeLabel) {
            throw badRequest("daily briefing must not expose internal time-window labels");
        }
        boolean hasForbiddenActionCopy = FORBIDDEN_ACTION_COPY.stream().anyMatch(lowered::contains);
        if (hasForbiddenActionCopy) {
            throw badRequest("daily briefing must not contain action advice copy");
        }
    }

    private RealEstateDailyBriefingResponse toResponse(RealEstateDailyBriefing briefing) {
        return new RealEstateDailyBriefingResponse(
                briefing.getId(),
                briefing.getBriefingDate(),
                briefing.getTitle(),
                readStringList(briefing.getSummaryHeadlinesJson()),
                briefing.getSections().stream().map(this::toSectionResponse).toList(),
                readMapList(briefing.getFocusRegionsJson()),
                briefing.getModelName(),
                briefing.getPromptVersion(),
                briefing.getGeneratedAt(),
                briefing.getSourceItems().stream().map(this::toSourceItemResponse).toList()
        );
    }

    private RealEstateDailyBriefingSectionResponse toSectionResponse(RealEstateDailyBriefingSection section) {
        return new RealEstateDailyBriefingSectionResponse(
                section.getSectionId(),
                section.getTitle(),
                section.getBody(),
                section.getDisplayOrder()
        );
    }

    private RealEstateDailyBriefingSourceItemResponse toSourceItemResponse(RealEstateDailyBriefingSourceItem sourceItem) {
        return new RealEstateDailyBriefingSourceItemResponse(
                sourceItem.getId().substring(sourceItem.getId().lastIndexOf(':') + 1),
                sourceItem.getSourceType(),
                sourceItem.getRefId(),
                sourceItem.getLabel(),
                sourceItem.getTitle(),
                sourceItem.getUrl(),
                sourceItem.getDisplayOrder()
        );
    }

    private List<String> normalizedHeadlines(List<String> values) {
        return values.stream()
                .map(RealEstateDailyBriefingService::trimToNull)
                .filter(value -> value != null)
                .toList();
    }

    private String writeStringList(List<String> values) {
        try {
            return objectMapper.writeValueAsString(values);
        } catch (JsonProcessingException exc) {
            throw new IllegalArgumentException("invalid daily briefing headlines", exc);
        }
    }

    private String writeMapList(List<Map<String, Object>> values) {
        try {
            return objectMapper.writeValueAsString(values);
        } catch (JsonProcessingException exc) {
            throw new IllegalArgumentException("invalid daily briefing focus regions", exc);
        }
    }

    private List<String> readStringList(String value) {
        try {
            return objectMapper.readValue(value, STRING_LIST);
        } catch (JsonProcessingException exc) {
            throw new IllegalStateException("invalid stored daily briefing headlines", exc);
        }
    }

    private List<Map<String, Object>> readMapList(String value) {
        try {
            return objectMapper.readValue(value, MAP_LIST);
        } catch (JsonProcessingException exc) {
            throw new IllegalStateException("invalid stored daily briefing focus regions", exc);
        }
    }

    private static String requireText(String value, String fieldName) {
        String trimmed = trimToNull(value);
        if (trimmed == null) {
            throw badRequest(fieldName + " is required");
        }
        return trimmed;
    }

    private static Instant requireInstant(Instant value, String fieldName) {
        if (value == null) {
            throw badRequest(fieldName + " is required");
        }
        return value;
    }

    private static String trimToNull(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private static ResponseStatusException badRequest(String message) {
        return new ResponseStatusException(HttpStatus.BAD_REQUEST, message);
    }
}
