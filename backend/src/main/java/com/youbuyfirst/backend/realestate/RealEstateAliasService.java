package com.youbuyfirst.backend.realestate;

import com.youbuyfirst.backend.realestate.dto.RealEstateAliasBatchResponse;
import com.youbuyfirst.backend.realestate.dto.RealEstateAliasRequest;
import com.youbuyfirst.backend.realestate.dto.RealEstateAliasResponse;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Objects;

@Service
public class RealEstateAliasService {

    private final RealEstateTargetRepository targetRepository;
    private final RealEstateAliasRepository aliasRepository;

    public RealEstateAliasService(
            RealEstateTargetRepository targetRepository,
            RealEstateAliasRepository aliasRepository
    ) {
        this.targetRepository = targetRepository;
        this.aliasRepository = aliasRepository;
    }

    @Transactional
    public RealEstateAliasBatchResponse upsertAliases(Collection<RealEstateAliasRequest> requests) {
        List<RealEstateAliasRequest> items = requests == null
                ? List.of()
                : requests.stream().filter(Objects::nonNull).toList();
        Instant now = Instant.now();
        int accepted = 0;
        int created = 0;
        int updated = 0;
        int skipped = 0;

        for (RealEstateAliasRequest item : items) {
            String aliasText = requireText(item.alias(), "alias");
            String normalizedAlias = RealEstateAlias.normalizeAlias(aliasText);
            if (normalizedAlias.length() < 2) {
                skipped++;
                continue;
            }

            String targetId = requireText(item.targetId(), "targetId");
            String targetType = normalizeLower(requireText(item.targetType(), "targetType"));
            RealEstateTarget target = targetRepository.findById(targetId)
                    .orElseThrow(() -> new IllegalArgumentException("real-estate target not found: " + targetId));
            if (!targetType.equals(normalizeLower(target.getTargetType()))) {
                throw new IllegalArgumentException("targetType does not match target: " + targetId);
            }

            String aliasType = normalizeLower(defaultIfBlank(item.aliasType(), "nickname"));
            String source = defaultIfBlank(item.source(), "import:unknown");
            String evidenceUrl = trimToNull(item.evidenceUrl());
            Double confidence = clampConfidence(item.confidence());
            String reviewState = normalizeLower(defaultIfBlank(item.reviewState(), "candidate"));
            Boolean ambiguous = Boolean.TRUE.equals(item.ambiguous());
            String createdBy = defaultIfBlank(item.createdBy(), "system");

            boolean[] isCreated = {false};
            RealEstateAlias alias = aliasRepository.findByTargetIdAndNormalizedAlias(targetId, normalizedAlias)
                    .orElseGet(() -> {
                        isCreated[0] = true;
                        return new RealEstateAlias(
                                targetId,
                                targetType,
                                aliasText.trim(),
                                aliasType,
                                source,
                                evidenceUrl,
                                confidence,
                                reviewState,
                                ambiguous,
                                createdBy,
                                now
                        );
                    });
            if (!isCreated[0]) {
                alias.update(
                        targetType,
                        aliasText.trim(),
                        aliasType,
                        source,
                        evidenceUrl,
                        confidence,
                        reviewState,
                        ambiguous,
                        createdBy,
                        now
                );
                updated++;
            } else {
                created++;
            }
            aliasRepository.save(alias);
            accepted++;
        }

        return new RealEstateAliasBatchResponse(accepted, created, updated, skipped);
    }

    @Transactional(readOnly = true)
    public List<RealEstateAliasResponse> publicAliasesForTarget(String targetId) {
        return aliasRepository
                .findByTargetIdAndReviewStateIgnoreCaseAndAmbiguousFalseOrderByAliasAsc(targetId, "approved")
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<RealEstateAliasResponse> aliasesForExport(
            String targetType,
            String reviewState,
            Boolean ambiguous,
            int limit
    ) {
        int boundedLimit = Math.max(1, Math.min(limit, 1000));
        return aliasRepository.findAliasesForExport(
                        trimToNull(targetType),
                        trimToNull(reviewState),
                        ambiguous,
                        PageRequest.of(0, boundedLimit)
                )
                .stream()
                .map(this::toResponse)
                .toList();
    }

    private RealEstateAliasResponse toResponse(RealEstateAlias alias) {
        return new RealEstateAliasResponse(
                alias.getId(),
                alias.getTargetType(),
                alias.getTargetId(),
                alias.getAlias(),
                alias.getNormalizedAlias(),
                alias.getAliasType(),
                alias.getSource(),
                alias.getEvidenceUrl(),
                alias.getConfidence(),
                alias.getReviewState(),
                alias.getCreatedBy(),
                alias.getAmbiguous()
        );
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
            return 0.5;
        }
        return Math.max(0.0, Math.min(1.0, value));
    }
}
