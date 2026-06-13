package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;

import java.util.List;

public record RealEstateEvidenceLogBatchRequest(
        @NotNull List<@Valid RealEstateEvidenceLogRequest> logs
) {
}
