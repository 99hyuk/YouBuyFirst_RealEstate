package com.youbuyfirst.backend.realestate.dto;

public record RealEstateEvidenceItemResponse(
        String evidenceItemId,
        String evidenceType,
        String refType,
        String refId,
        String label,
        String valueText,
        String severity
) {
}
