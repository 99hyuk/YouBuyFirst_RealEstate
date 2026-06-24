package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;

import java.util.List;

public record RealEstateDailyBriefingBatchRequest(
        @NotNull List<@Valid RealEstateDailyBriefingRequest> briefings
) {
}
