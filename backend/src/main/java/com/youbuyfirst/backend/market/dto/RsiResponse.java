package com.youbuyfirst.backend.market.dto;

import java.util.List;

public record RsiResponse(
        int period,
        List<RsiPointResponse> points
) {
}
