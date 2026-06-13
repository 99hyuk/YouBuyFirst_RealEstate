package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateEvidenceLogListResponse(
        List<RealEstateEvidenceLogResponse> items
) {
}
