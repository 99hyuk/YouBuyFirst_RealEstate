package com.youbuyfirst.backend.market.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;

import java.util.List;

public record InvestorFlowBatchRequest(
        @NotEmpty List<@Valid InvestorFlowSnapshotRequest> items
) {
}
