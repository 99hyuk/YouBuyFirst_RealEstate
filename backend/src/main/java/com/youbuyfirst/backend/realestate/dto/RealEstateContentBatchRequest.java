package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;

import java.util.List;

public record RealEstateContentBatchRequest(
        @NotNull List<@Valid RealEstateContentItemRequest> items
) {
}
