package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record RealEstateIndicatorOverviewResponse(
        String period,
        String dataStatus,
        String asOf,
        List<Group> groups,
        List<FreshnessRow> freshnessRows
) {
    public record Group(
            String id,
            String label,
            String title,
            String headline,
            String change,
            String tone,
            String summary,
            List<String> chips,
            List<Metric> metrics,
            String dataStatus,
            boolean stale,
            String provider,
            String asOf
    ) {
    }

    public record Metric(
            String name,
            String value,
            String tone
    ) {
    }

    public record FreshnessRow(
            String source,
            String state,
            String used
    ) {
    }
}
