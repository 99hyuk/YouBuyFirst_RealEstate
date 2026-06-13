package com.youbuyfirst.backend.realestate.dto;

import java.time.Instant;
import java.util.List;

public record RealEstateEvidenceLogResponse(
        String evidenceLogId,
        String targetId,
        Long snapshotId,
        String evaluationVersion,
        String promptVersion,
        String modelName,
        String tone,
        String summary,
        String subtitle,
        List<String> caveats,
        String dataQuality,
        Double confidence,
        String skipReason,
        Instant evaluatedAt,
        Instant asOf,
        List<RealEstateEvidenceItemResponse> evidenceItems
) {
}
