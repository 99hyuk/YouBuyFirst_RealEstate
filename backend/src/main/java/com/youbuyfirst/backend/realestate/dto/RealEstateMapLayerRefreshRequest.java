package com.youbuyfirst.backend.realestate.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;
import java.util.List;

public record RealEstateMapLayerRefreshRequest(
        @NotBlank String layerType,
        @NotEmpty List<@NotBlank String> periods,
        @NotNull Instant asOf
) {
}
