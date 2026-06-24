package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record MarketDataScheduleResponse(
        String month,
        List<MarketDataScheduleEventResponse> scheduleEvents,
        List<MarketDataSourceLinkResponse> sourceLinks
) {
}
