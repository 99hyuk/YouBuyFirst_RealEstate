package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;

import java.util.List;

public record PolicyEventBatchRequest(
        @NotEmpty List<@Valid PolicyEventRequest> items
) {
}
