package com.youbuyfirst.backend.indicator;

public record RealEstateReactionRatioResponse(
        double expectation,
        double concern,
        double neutral
) {
}
