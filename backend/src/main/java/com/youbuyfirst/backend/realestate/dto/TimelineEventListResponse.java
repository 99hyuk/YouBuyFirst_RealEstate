package com.youbuyfirst.backend.realestate.dto;

import java.util.List;

public record TimelineEventListResponse(
        List<TimelineEventResponse> items
) {
}
