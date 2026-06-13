package com.youbuyfirst.backend.indicator;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;

import java.util.List;

public record RealEstateReactionSnapshotBatchRequest(
        @NotEmpty List<@Valid RealEstateReactionSnapshotRequest> items
) {
}
